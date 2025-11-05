#!/usr/bin/env python3
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QPlainTextEdit,
    QFileDialog,
    QProgressBar,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QWidget,
)
from PySide6.QtGui import QColor, QBrush

import re
import shutil


def _natural_key(path: Path):
    name = path.name
    tok = re.split(r"(\d+)", name)
    key = []
    for t in tok:
        key.append(int(t) if t.isdigit() else t.lower())
    return key


def list_images(folder: Path, pattern: str):
    # 하위 폴더까지 재귀적으로 탐색
    paths = [p for p in folder.rglob(pattern) if p.is_file()]
    return sorted(paths, key=_natural_key)

def build_new_name(
    index_value: int,
    suffix: str,
    pad_width: int,
    index_mul: float,
    index_offset: int,
    prefix: str,
    postfix: str,
):
    mul = 0.0 if index_mul is None else float(index_mul)
    off = 0 if index_offset is None else index_offset
    computed_float = index_value * mul + off
    computed = int(round(computed_float))
    if pad_width is None or pad_width < 0:
        pad_width = 0
    if pad_width == 0:
        num_str = f"{computed}"
    else:
        num_str = f"{computed:0{pad_width}d}"

    px = (prefix or "").strip()
    if px:
        sep = "" if px.endswith(("_", "-")) else "_"
        base = f"{px}{sep}{num_str}"
    else:
        base = num_str

    post = (postfix or "").strip()
    if post:
        sep2 = "" if post.startswith(("_", "-")) else "_"
        base = f"{base}{sep2}{post}"

    return f"{base}{suffix}"


def build_keep_name(original_stem: str, suffix: str, prefix: str, postfix: str):
    """원본 파일명을 유지하면서 prefix와 postfix를 추가"""
    px = (prefix or "").strip()
    post = (postfix or "").strip()
    
    # prefix 추가
    if px:
        sep = "" if px.endswith(("_", "-")) else "_"
        base = f"{px}{sep}{original_stem}"
    else:
        base = original_stem
    
    # postfix 추가
    if post:
        sep2 = "" if post.startswith(("_", "-")) else "_"
        base = f"{base}{sep2}{post}"
    
    return f"{base}{suffix}"


def ensure_write(src: Path, dst: Path, *, move: bool, overwrite: bool, dry_run: bool, verbose: bool):
    if dst.exists():
        if overwrite:
            if verbose:
                print(f"[overwrite] {dst}")
            if not dry_run and dst.is_file():
                dst.unlink()
        else:
            if verbose:
                print(f"[skip] 대상 파일 이미 존재: {dst}")
            return
    if verbose:
        action = "move" if move else "copy"
        print(f"[{action}] {src.name} -> {dst.name}")
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if move:
        # cross-device 이동 지원
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(src, dst)


class Worker(QObject):
    progressed = Signal(str)
    progress = Signal(int, int)  # current, total
    finished = Signal(int, int)
    failed = Signal(str)

    def __init__(
        self,
        folder: Path,
        pattern: str,
        rename_mode: str,
        index_base: int,
        pad_width: int,
        index_mul: int,
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
        self.folder = folder
        self.pattern = pattern
        self.rename_mode = rename_mode
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

    @Slot()
    def run(self) -> None:
        try:
            if not self.folder.exists() or not self.folder.is_dir():
                self.failed.emit("폴더 경로가 유효하지 않습니다.")
                return

            paths = list_images(self.folder, self.pattern)
            if len(paths) == 0:
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
                    group_paths = sorted(groups[key], key=_natural_key)
                    for idx, gp in enumerate(group_paths):
                        i = idx + self.index_base
                        pairs.append((gp, i))

            # 선택 규칙 필터 적용
            if self.apply_selection and self.sel_division and self.sel_division > 0:
                pairs = [ (p, i) for (p, i) in pairs if (i - self.sel_offset) % self.sel_division == 0 ]

            if len(pairs) == 0:
                self.finished.emit(0, 0)
                return

            count_ok = 0
            count_total = len(pairs)

            # 초기 진행률 알림
            self.progress.emit(0, count_total)

            # 캡처하여 로그 위젯으로 전달
            buf = io.StringIO()
            with redirect_stdout(buf):
                for src, index_value in pairs:
                    suffix = src.suffix
                    # 이름 변경 모드에 따라 다른 함수 사용
                    if self.rename_mode == "현재 이름 유지":
                        new_name = build_keep_name(
                            src.stem,
                            suffix,
                            self.prefix,
                            self.postfix,
                        )
                    else:
                        new_name = build_new_name(
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

                    # 실제 쓰기 (ensure_write 내부 로그는 끔 - 중복 방지)
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

            self.finished.emit(count_ok, count_total)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class RenamerWindow(QMainWindow):
    """파일명 변경 도구 GUI"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("파일명 변경 도구")
        self._build_ui()
        self._connect()

        self.thread: QThread | None = None
        self.worker: Worker | None = None

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        # Inputs
        self.edit_folder = QLineEdit()
        self.btn_browse = QPushButton("폴더 선택")
        self.edit_pattern = QLineEdit("*.bmp")

        # 이름 변경 모드 선택
        self.combo_rename_mode = QComboBox()
        self.combo_rename_mode.addItems(["새로운 규칙으로 변경", "현재 이름 유지"])
        self.combo_rename_mode.setCurrentIndex(0)

        # 선택 규칙 제거: 모든 파일 대상 처리

        self.combo_index_base = QComboBox()
        self.combo_index_base.addItems(["1", "0"])  # 기본 1
        self.combo_index_base.setCurrentIndex(0)

        self.edit_prefix = QLineEdit("frame")
        self.edit_postfix = QLineEdit("")

        self.spin_pad = QSpinBox()
        self.spin_pad.setRange(0, 12)
        self.spin_pad.setValue(4)

        # 이름 계산 파라미터 (기본: i*2 + 0)
        self.spin_index_mul = QDoubleSpinBox()
        self.spin_index_mul.setDecimals(6)
        self.spin_index_mul.setRange(-1e6, 1e6)
        self.spin_index_mul.setValue(1.0)

        self.spin_index_offset = QSpinBox()
        self.spin_index_offset.setRange(-999999, 999999)
        self.spin_index_offset.setValue(0)

        self.chk_move = QCheckBox("이동(이름 변경)")
        self.chk_overwrite = QCheckBox("덮어쓰기")
        self.chk_dry = QCheckBox("드라이런")
        self.chk_dry.setChecked(False)
        self.chk_verbose = QCheckBox("자세한 로그")
        self.chk_verbose.setChecked(True)

        self.chk_reset_per_folder = QCheckBox("폴더별 인덱스 초기화")
        self.chk_reset_per_folder.setChecked(False)

        # 출력 모드: 원본 위치 / 구조 유지하여 다른 폴더
        self.combo_output_mode = QComboBox()
        self.combo_output_mode.addItems(["원본 위치", "다른 폴더(구조 유지)"])
        self.edit_dst = QLineEdit("")
        self.btn_dst_browse = QPushButton("결과 폴더 선택")
        dst_row = QHBoxLayout()
        dst_row.addWidget(self.edit_dst)
        dst_row.addWidget(self.btn_dst_browse)
        self.dst_box = QWidget()
        self.dst_box.setLayout(dst_row)

        form = QFormLayout()
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.edit_folder)
        folder_row.addWidget(self.btn_browse)
        folder_box = QWidget()
        folder_box.setLayout(folder_row)

        form.addRow("폴더", folder_box)
        form.addRow("패턴", self.edit_pattern)
        form.addRow("이름 변경 모드", self.combo_rename_mode)
        form.addRow("출력 모드", self.combo_output_mode)
        form.addRow("결과 폴더", self.dst_box)

        opts = QHBoxLayout()
        opts.addWidget(self.chk_move)
        opts.addWidget(self.chk_overwrite)
        opts.addWidget(self.chk_dry)
        opts.addWidget(self.chk_verbose)
        opts.addWidget(self.chk_reset_per_folder)
        opts_box = QWidget()
        opts_box.setLayout(opts)
        form.addRow("옵션", opts_box)

        # Actions
        self.btn_preview = QPushButton("미리보기")
        self.btn_run = QPushButton("실행")
        self.btn_clear = QPushButton("로그 삭제")
        actions = QHBoxLayout()
        actions.addWidget(self.btn_preview)
        actions.addWidget(self.btn_run)
        actions.addWidget(self.btn_clear)
        actions_box = QWidget()
        actions_box.setLayout(actions)

        # Log
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)

        # 선택 및 미리보기
        self.group_select = QGroupBox("선택 및 미리보기")
        sel_layout = QFormLayout()
        self.btn_scan = QPushButton("불러오기")
        self.chk_apply_selection = QCheckBox("선택 규칙 적용")
        self.chk_apply_selection.setChecked(False)
        self.spin_sel_offset = QSpinBox()
        self.spin_sel_offset.setRange(-999999, 999999)
        self.spin_sel_offset.setValue(1)
        self.spin_sel_div = QSpinBox()
        self.spin_sel_div.setRange(1, 999999)
        self.spin_sel_div.setValue(3)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Index", "RelDir", "File"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        sel_layout.addRow("불러오기", self.btn_scan)
        sel_layout.addRow("규칙 적용", self.chk_apply_selection)
        sel_layout.addRow("sel-offset", self.spin_sel_offset)
        sel_layout.addRow("sel-division", self.spin_sel_div)
        sel_layout.addRow(self.tree)
        self.group_select.setLayout(sel_layout)

        # 파일 이름 규칙
        self.group_rename = QGroupBox("파일 이름 규칙")
        rename_layout = QFormLayout()
        rename_layout.addRow("index-base", self.combo_index_base)
        rename_layout.addRow("prefix", self.edit_prefix)
        rename_layout.addRow("postfix", self.edit_postfix)
        rename_layout.addRow("pad-width", self.spin_pad)
        rename_layout.addRow("index-mul", self.spin_index_mul)
        rename_layout.addRow("index-offset", self.spin_index_offset)
        self.group_rename.setLayout(rename_layout)

        # 실행 및 로그
        grid = QGridLayout()
        grid.addLayout(form, 0, 0)
        grid.addWidget(self.group_select, 1, 0)
        grid.addWidget(self.group_rename, 2, 0)
        grid.addWidget(actions_box, 3, 0)
        grid.addWidget(self.progress, 4, 0)
        grid.addWidget(self.log, 5, 0)
        central.setLayout(grid)

        # 선택 규칙이 제거되어 추가 초기화 필요 없음

    def _connect(self) -> None:
        self.btn_browse.clicked.connect(self._on_browse)
        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_run.clicked.connect(self._on_run)
        self.btn_clear.clicked.connect(self._on_clear_log)
        self.btn_dst_browse.clicked.connect(self._on_browse_dst)
        self.combo_output_mode.currentIndexChanged.connect(self._update_output_mode)
        self.combo_rename_mode.currentIndexChanged.connect(self._update_rename_mode)
        self.btn_scan.clicked.connect(self._on_scan)
        self.spin_sel_offset.valueChanged.connect(self._on_selection_changed)
        self.spin_sel_div.valueChanged.connect(self._on_selection_changed)
        self.chk_apply_selection.toggled.connect(self._on_selection_changed)
        self.combo_index_base.currentIndexChanged.connect(self._on_selection_changed)
        self.chk_reset_per_folder.toggled.connect(self._on_selection_changed)

        self._update_output_mode()
        self._update_rename_mode()

    @Slot()
    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if path:
            self.edit_folder.setText(path)

    def _validate(self) -> tuple[Path, str, str, int, int, int, int, str, str, bool, int, int, bool, bool, Path | None, bool, bool, bool, bool] | None:
        folder = Path(self.edit_folder.text().strip())
        pattern = self.edit_pattern.text().strip() or "*"
        rename_mode = self.combo_rename_mode.currentText()
        index_base = 1 if self.combo_index_base.currentText() == "1" else 0
        pad_width = int(self.spin_pad.value())
        index_mul = float(self.spin_index_mul.value())
        index_offset = int(self.spin_index_offset.value())
        prefix = self.edit_prefix.text()
        postfix = self.edit_postfix.text()
        apply_selection = self.chk_apply_selection.isChecked()
        sel_offset = int(self.spin_sel_offset.value())
        sel_division = int(self.spin_sel_div.value())
        reset_per_folder = self.chk_reset_per_folder.isChecked()
        preserve_tree = self.combo_output_mode.currentIndex() == 1
        dest_root: Path | None = None
        if preserve_tree:
            dst_text = self.edit_dst.text().strip()
            if not dst_text:
                QMessageBox.warning(self, "경고", "결과 폴더를 선택하세요.")
                return None
            dest_root = Path(dst_text)
        move = self.chk_move.isChecked()
        overwrite = self.chk_overwrite.isChecked()
        dry_run = self.chk_dry.isChecked()
        verbose = self.chk_verbose.isChecked()

        if not folder.exists() or not folder.is_dir():
            QMessageBox.warning(self, "경고", "유효한 폴더를 선택하세요.")
            return None

        return (
            folder,
            pattern,
            rename_mode,
            index_base,
            pad_width,
            index_mul,
            index_offset,
            prefix,
            postfix,
            apply_selection,
            sel_offset,
            sel_division,
            reset_per_folder,
            preserve_tree,
            dest_root,
            move,
            overwrite,
            dry_run,
            verbose,
        )

    def _start_worker(self, *, dry_run_override: bool | None = None) -> None:
        validated = self._validate()
        if not validated:
            return

        (
            folder,
            pattern,
            rename_mode,
            index_base,
            pad_width,
            index_mul,
            index_offset,
            prefix,
            postfix,
            apply_selection,
            sel_offset,
            sel_division,
            reset_per_folder,
            preserve_tree,
            dest_root,
            move,
            overwrite,
            dry_run,
            verbose,
        ) = validated

        if dry_run_override is not None:
            dry_run = dry_run_override

        self._set_running(True)
        self.log.appendPlainText("작업 시작...")

        self.thread = QThread(self)
        self.worker = Worker(
            folder=folder,
            pattern=pattern,
            rename_mode=rename_mode,
            index_base=index_base,
            pad_width=pad_width,
            index_mul=index_mul,
            index_offset=index_offset,
            prefix=prefix,
            postfix=postfix,
            apply_selection=apply_selection,
            sel_offset=sel_offset,
            sel_division=sel_division,
            reset_per_folder=reset_per_folder,
            preserve_tree=preserve_tree,
            dest_root=dest_root,
            move=move,
            overwrite=overwrite,
            dry_run=dry_run,
            verbose=verbose,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progressed.connect(self._on_progress)
        self.worker.progress.connect(self._on_progress_update)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.thread.start()

    @Slot()
    def _on_preview(self) -> None:
        self._start_worker(dry_run_override=True)

    @Slot()
    def _on_run(self) -> None:
        self._start_worker(dry_run_override=None)

    @Slot(str)
    def _on_progress(self, text: str) -> None:
        if text:
            self.log.appendPlainText(text.rstrip("\n"))

    @Slot(int, int)
    def _on_progress_update(self, current: int, total: int) -> None:
        if total <= 0:
            self.progress.setRange(0, 0)
            return
        # 첫 호출에서 유한 범위 설정
        self.progress.setRange(0, total)
        self.progress.setValue(current)

    @Slot()
    def _on_clear_log(self) -> None:
        self.log.clear()

    @Slot()
    def _on_browse_dst(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "결과 폴더 선택")
        if path:
            self.edit_dst.setText(path)

    def _update_output_mode(self) -> None:
        is_preserve = self.combo_output_mode.currentIndex() == 1
        self.dst_box.setEnabled(is_preserve)
        self.dst_box.setVisible(is_preserve)

    def _update_rename_mode(self) -> None:
        is_new_rule = self.combo_rename_mode.currentText() == "새로운 규칙으로 변경"
        # 새로운 규칙으로 변경 시에만 인덱스 관련 컨트롤 활성화
        self.combo_index_base.setEnabled(is_new_rule)
        self.spin_pad.setEnabled(is_new_rule)
        self.spin_index_mul.setEnabled(is_new_rule)
        self.spin_index_offset.setEnabled(is_new_rule)
        self.chk_reset_per_folder.setEnabled(is_new_rule)

    # ---------- Scan & Tree Highlight ----------
    def _compute_pairs_for_ui(self, paths: list[Path]) -> list[tuple[Path, int]]:
        if not self.chk_reset_per_folder.isChecked():
            base = 1 if self.combo_index_base.currentText() == "1" else 0
            return [(p, idx + base) for idx, p in enumerate(paths)]
        groups: dict[str, list[Path]] = {}
        folder = Path(self.edit_folder.text().strip())
        for p in paths:
            try:
                rel_parent = p.parent.relative_to(folder)
            except Exception:
                rel_parent = Path("")
            key = str(rel_parent)
            groups.setdefault(key, []).append(p)
        pairs: list[tuple[Path, int]] = []
        base = 1 if self.combo_index_base.currentText() == "1" else 0
        for key in sorted(groups.keys(), key=lambda s: s.lower()):
            group_paths = sorted(groups[key], key=_natural_key)
            for idx, gp in enumerate(group_paths):
                pairs.append((gp, idx + base))
        return pairs

    def _on_scan(self) -> None:
        folder = Path(self.edit_folder.text().strip())
        pattern = self.edit_pattern.text().strip() or "*"
        if not folder.exists() or not folder.is_dir():
            QMessageBox.warning(self, "경고", "유효한 폴더를 선택하세요.")
            return
        paths = list_images(folder, pattern)
        self._populate_tree(paths)
        self._highlight_tree()

    def _populate_tree(self, paths: list[Path]) -> None:
        self.tree.clear()
        folder = Path(self.edit_folder.text().strip())
        # group by relative parent
        groups: dict[str, list[Path]] = {}
        for p in paths:
            try:
                rel_parent = p.parent.relative_to(folder)
            except Exception:
                rel_parent = Path("")
            key = str(rel_parent)
            groups.setdefault(key, []).append(p)
        base = 1 if self.combo_index_base.currentText() == "1" else 0
        for key in sorted(groups.keys(), key=lambda s: s.lower()):
            parent_item = QTreeWidgetItem(["", key if key else ".", ""])  # folder row
            self.tree.addTopLevelItem(parent_item)
            for idx, p in enumerate(sorted(groups[key], key=_natural_key)):
                i = idx + base
                child = QTreeWidgetItem([str(i), key if key else ".", p.name])
                child.setData(0, Qt.UserRole, i)
                child.setData(1, Qt.UserRole, str(p))
                parent_item.addChild(child)
            parent_item.setExpanded(True)

    def _highlight_tree(self) -> None:
        apply_sel = self.chk_apply_selection.isChecked()
        sel_off = int(self.spin_sel_offset.value())
        sel_div = int(self.spin_sel_div.value())
        # colors
        hl_brush = QBrush(QColor(255, 255, 200))
        normal_brush = QBrush()
        for t in range(self.tree.topLevelItemCount()):
            parent_item = self.tree.topLevelItem(t)
            for c in range(parent_item.childCount()):
                item = parent_item.child(c)
                i = int(item.data(0, Qt.UserRole) or 0)
                selected = apply_sel and sel_div > 0 and ((i - sel_off) % sel_div == 0)
                for col in range(3):
                    item.setBackground(col, hl_brush if selected else normal_brush)

    def _on_selection_changed(self) -> None:
        # If nothing loaded yet, perform a scan for preview convenience
        if self.tree.topLevelItemCount() == 0:
            self._on_scan()
            return
        self._highlight_tree()

    @Slot(int, int)
    def _on_finished(self, ok: int, total: int) -> None:
        self.log.appendPlainText(f"완료: {ok}/{total}")
        self._cleanup_worker()
        self._set_running(False)

    @Slot(str)
    def _on_failed(self, msg: str) -> None:
        self.log.appendPlainText(f"오류: {msg}")
        self._cleanup_worker()
        self._set_running(False)

    def _cleanup_worker(self) -> None:
        if self.thread and self.worker:
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None

    def _set_running(self, running: bool) -> None:
        for w in [
            self.edit_folder,
            self.btn_browse,
            self.edit_pattern,
            self.combo_rename_mode,
            self.combo_index_base,
            self.edit_prefix,
            self.edit_postfix,
            self.spin_pad,
            self.spin_index_mul,
            self.spin_index_offset,
            self.combo_output_mode,
            self.edit_dst,
            self.btn_dst_browse,
            self.chk_move,
            self.chk_overwrite,
            self.chk_dry,
            self.chk_verbose,
            self.chk_reset_per_folder,
            self.btn_preview,
            self.btn_run,
        ]:
            w.setEnabled(not running)


def main() -> None:
    """독립 실행용 (테스트)"""
    app = QApplication(sys.argv)
    win = RenamerWindow()
    win.resize(800, 600)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

