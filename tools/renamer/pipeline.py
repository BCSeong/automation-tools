"""Renamer 도구의 연산 Pipeline"""
from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from tools.common.file_utils import ensure_write, list_files
from tools.common.path_utils import natural_sort_key
from tools.common.log_utils import get_tool_logger
from tools.renamer.functions import build_new_name, build_keep_name


class RenamerWorker(QObject):
    """파일명 변경 작업을 처리하는 Worker (Pipeline)"""
    progressed = Signal(str)
    progress = Signal(int, int)  # current, total
    finished = Signal(int, int)
    failed = Signal(str)

    def __init__(
        self,
        folder: Path,
        pattern: str,
        rename_method: str,  # 메서드명 (예: "build_new_name", "build_keep_name")
        index_base: int,
        pad_width: int,
        index_mul: float,
        index_offset: int,
        prefix: str,
        postfix: str,
        apply_selection: bool,
        sel_offset: int,
        sel_division: int,
        reset_per_folder: bool,
        preserve_tree: bool,
        dest_root: Path | None,
        move: bool,
        overwrite: bool,
        dry_run: bool,
        verbose: bool,
    ) -> None:
        super().__init__()
        self.logger = get_tool_logger("renamer")
        self.folder = folder
        self.pattern = pattern
        self.rename_method = rename_method
        self.index_base = index_base
        self.pad_width = pad_width
        self.index_mul = index_mul
        self.index_offset = index_offset
        self.prefix = prefix
        self.postfix = postfix
        self.apply_selection = apply_selection
        self.sel_offset = sel_offset
        self.sel_division = sel_division
        self.reset_per_folder = reset_per_folder
        self.preserve_tree = preserve_tree
        self.dest_root = dest_root
        self.move = move
        self.overwrite = overwrite
        self.dry_run = dry_run
        self.verbose = verbose

    def _get_build_function(self):
        """메서드명으로 파일명 생성 함수 반환"""
        method_map = {
            "build_new_name": build_new_name,
            "build_keep_name": build_keep_name,
        }
        return method_map.get(self.rename_method, build_new_name)  # 기본값

    @Slot()
    def run(self) -> None:
        """작업 실행"""
        try:
            self.logger.info("Renaming task started: folder=%s, pattern=%s, method=%s", 
                           self.folder, self.pattern, self.rename_method)
            
            if not self.folder.exists() or not self.folder.is_dir():
                error_msg = f"Invalid folder path: {self.folder}"
                self.logger.error(error_msg)
                self.failed.emit("폴더 경로가 유효하지 않습니다.")
                return

            # 범용 함수 사용
            paths = list_files(self.folder, self.pattern, recursive=True)
            self.logger.debug("Found %d files matching pattern '%s'", len(paths), self.pattern)
            
            if len(paths) == 0:
                self.logger.warning("No files found matching pattern '%s' in folder: %s", 
                                  self.pattern, self.folder)
                self.finished.emit(0, 0)
                return

            if not self.reset_per_folder:
                pairs = [(p, idx + self.index_base) for idx, p in enumerate(paths)]
            else:
                # 폴더별로 인덱스 초기화
                groups: dict[str, list[Path]] = {}
                for p in paths:
                    try:
                        rel_parent = p.parent.relative_to(self.folder)
                    except Exception:
                        rel_parent = Path("")
                    key = str(rel_parent)
                    groups.setdefault(key, []).append(p)

                pairs = []
                for key in sorted(groups.keys(), key=lambda s: s.lower()):
                    group_paths = sorted(groups[key], key=natural_sort_key)
                    for idx, gp in enumerate(group_paths):
                        i = idx + self.index_base
                        pairs.append((gp, i))

            # 선택 규칙 필터 적용
            if self.apply_selection and self.sel_division and self.sel_division > 0:
                original_count = len(pairs)
                pairs = [ (p, i) for (p, i) in pairs if (i - self.sel_offset) % self.sel_division == 0 ]
                self.logger.debug("Selection filter applied: %d -> %d files", 
                                original_count, len(pairs))

            if len(pairs) == 0:
                self.logger.warning("No files to process after filtering")
                self.finished.emit(0, 0)
                return

            count_ok = 0
            count_total = len(pairs)
            self.logger.info("Processing %d files (move=%s, overwrite=%s, dry_run=%s)", 
                           count_total, self.move, self.overwrite, self.dry_run)

            # 초기 진행률 알림
            self.progress.emit(0, count_total)

            # 파일명 생성 함수 가져오기
            build_func = self._get_build_function()

            # 캡처하여 로그 위젯으로 전달
            buf = io.StringIO()
            with redirect_stdout(buf):
                for src, index_value in pairs:
                    suffix = src.suffix
                    # 메서드명에 따라 적절한 함수 호출
                    if self.rename_method == "build_keep_name":
                        # 현재 이름 유지 모드
                        new_name = build_func(
                            src.stem,
                            suffix,
                            self.prefix,
                            self.postfix,
                        )
                    else:
                        # 새로운 규칙으로 변경 모드 (기본값)
                        new_name = build_func(
                            index_value,
                            suffix,
                            self.pad_width,
                            self.index_mul,
                            self.index_offset,
                            self.prefix,
                            self.postfix,
                        )
                    
                    if self.preserve_tree and self.dest_root is not None:
                        try:
                            rel_parent = src.parent.relative_to(self.folder)
                        except Exception:
                            rel_parent = Path("")
                        dst_dir = self.dest_root / rel_parent
                        dst = dst_dir / new_name
                    else:
                        dst = src.with_name(new_name)

                    # 로그: 선택 폴더 기준 상대 경로(모든 상위 폴더)와 목적지 상대 경로 표시
                    if self.verbose or self.dry_run:
                        action = "move" if self.move else "copy"
                        try:
                            rel_parent_for_log = src.parent.relative_to(self.folder)
                        except Exception:
                            rel_parent_for_log = Path("")
                        rel_dir_str = str(rel_parent_for_log).replace("\\", "/") or "."
                        dest_rel_path = f"{rel_dir_str}/{new_name}" if rel_dir_str != "." else new_name

                        if dst.exists():
                            if not self.overwrite:
                                print(f"[skip] {rel_dir_str} | {src.name} -> {dest_rel_path}")
                            else:
                                print(f"[overwrite] {rel_dir_str} | {src.name} -> {dest_rel_path}")
                        else:
                            print(f"[{action}] {rel_dir_str} | {src.name} -> {dest_rel_path}")

                    # 실제 쓰기 (범용 함수 사용)
                    ensure_write(
                        src,
                        dst,
                        move=self.move,
                        overwrite=self.overwrite,
                        dry_run=self.dry_run,
                        verbose=False,
                    )

                    count_ok += 1
                    self.progress.emit(count_ok, count_total)

            text = buf.getvalue()
            if text:
                self.progressed.emit(text)

            self.logger.info("Task completed: %d/%d files processed successfully", 
                           count_ok, count_total)
            self.finished.emit(count_ok, count_total)
        except Exception as e:  # noqa: BLE001
            self.logger.error("Task failed: %s", str(e), exc_info=True)
            self.failed.emit(str(e))


# CLI 테스트 지원
if __name__ == "__main__":
    import sys
    import argparse
    from PySide6.QtCore import QCoreApplication, QThread
    
    parser = argparse.ArgumentParser(description="Renamer Pipeline 테스트")
    parser.add_argument('--folder', type=str, required=True, help='대상 폴더 경로')
    parser.add_argument('--pattern', type=str, default='*.bmp', help='파일 패턴')
    parser.add_argument('--rename-method', type=str, choices=['build_new_name', 'build_keep_name'], 
                        default='build_new_name', help='파일명 생성 메서드')
    parser.add_argument('--index-base', type=int, default=1, help='인덱스 시작값')
    parser.add_argument('--pad-width', type=int, default=4, help='숫자 패딩 너비')
    parser.add_argument('--index-mul', type=float, default=1.0, help='인덱스 곱셈')
    parser.add_argument('--index-offset', type=int, default=0, help='인덱스 오프셋')
    parser.add_argument('--prefix', type=str, default='frame', help='파일명 prefix')
    parser.add_argument('--postfix', type=str, default='', help='파일명 postfix')
    parser.add_argument('--apply-selection', action='store_true', help='선택 규칙 적용')
    parser.add_argument('--sel-offset', type=int, default=0, help='선택 오프셋')
    parser.add_argument('--sel-division', type=int, default=0, help='선택 나눗셈')
    parser.add_argument('--reset-per-folder', action='store_true', help='폴더별 인덱스 초기화')
    parser.add_argument('--preserve-tree', action='store_true', help='폴더 구조 유지')
    parser.add_argument('--dest-root', type=str, help='대상 폴더 (preserve-tree 사용 시 필수)')
    parser.add_argument('--move', action='store_true', help='이동 (기본값: 복사)')
    parser.add_argument('--overwrite', action='store_true', help='덮어쓰기')
    parser.add_argument('--dry-run', action='store_true', help='실제 작업 없이 미리보기')
    parser.add_argument('--verbose', action='store_true', help='상세 로그')
    
    args = parser.parse_args()
    
    folder = Path(args.folder)
    if not folder.exists() or not folder.is_dir():
        print(f"Error: 유효한 폴더가 아닙니다: {folder}")
        sys.exit(1)
    
    dest_root = Path(args.dest_root) if args.dest_root else None
    if args.preserve_tree and not dest_root:
        print("Error: --preserve-tree 사용 시 --dest-root가 필요합니다")
        sys.exit(1)
    
    # QApplication 생성 (GUI 없이)
    app = QCoreApplication(sys.argv)
    
    # Worker 생성
    worker = RenamerWorker(
        folder=folder,
        pattern=args.pattern,
        rename_method=args.rename_method,
        index_base=args.index_base,
        pad_width=args.pad_width,
        index_mul=args.index_mul,
        index_offset=args.index_offset,
        prefix=args.prefix,
        postfix=args.postfix,
        apply_selection=args.apply_selection,
        sel_offset=args.sel_offset,
        sel_division=args.sel_division,
        reset_per_folder=args.reset_per_folder,
        preserve_tree=args.preserve_tree,
        dest_root=dest_root,
        move=args.move,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    
    # 시그널 연결
    def on_progressed(text: str):
        print(text, end='')
    
    def on_progress(current: int, total: int):
        print(f"\r진행률: {current}/{total} ({current*100//total if total > 0 else 0}%)", end='', flush=True)
    
    def on_finished(ok: int, total: int):
        print(f"\n완료: {ok}/{total} 파일 처리됨")
        app.quit()
    
    def on_failed(msg: str):
        print(f"\n오류: {msg}")
        app.quit()
    
    worker.progressed.connect(on_progressed)
    worker.progress.connect(on_progress)
    worker.finished.connect(on_finished)
    worker.failed.connect(on_failed)
    
    # Worker를 스레드에서 실행
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    thread.finished.connect(app.quit)
    thread.start()
    
    print(f"작업 시작: {folder} (패턴: {args.pattern})")
    if args.dry_run:
        print("*** DRY RUN 모드: 실제 파일 변경 없음 ***")
    print("-" * 50)
    
    app.exec()
    
    thread.quit()
    thread.wait()
    
    print("-" * 50)
    print("테스트 완료")

