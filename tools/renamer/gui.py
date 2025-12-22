#!/usr/bin/env python3
"""Renamer 도구의 GUI"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QHeaderView,
    QTreeWidgetItem,
)
from PySide6.QtGui import QColor, QBrush

from tools.common.file_utils import list_files
from tools.common.path_utils import natural_sort_key
from tools.common.ui_utils import load_ui_file
from tools.common.log_utils import get_tool_logger
from tools.renamer.pipeline import RenamerWorker


class RenamerWindow(QMainWindow):
    """파일명 변경 도구 GUI"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.logger = get_tool_logger("renamer")
        self.constants = self._load_constants()
        self._load_ui()
        self._apply_config_to_ui()
        self._connect()

        self.thread: QThread | None = None
        self.worker: RenamerWorker | None = None
        self.logger.info("RenamerWindow initialized")

    def _load_constants(self) -> dict:
        """constants.json 로드"""
        config_path = Path(__file__).parent / 'constants.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_ui(self) -> None:
        """Designer .ui 파일 로드
        
        공통 유틸리티 함수를 사용하여 간단하게 UI를 로드합니다.
        Designer에서 설정한 objectName으로 위젯에 접근할 수 있습니다.
        """
        ui_path = Path(__file__).parent / 'ui' / 'main.ui'
        load_ui_file(ui_path, self)
        # .ui 파일에서 설정한 기본값이 자동 적용됨
        
        # Tree (파일명을 보여주는 table)의 위젯 헤더 설정 (Designer에서 완전히 설정 불가)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # 현재 폴더 구조 트리 설정
        if hasattr(self, 'tree_current_structure'):
            self.tree_current_structure.setHeaderLabel("파일/폴더")
            self.tree_current_structure.setRootIsDecorated(True)
        
        # 미리보기 트리 설정
        if hasattr(self, 'tree_preview_structure'):
            self.tree_preview_structure.setHeaderLabel("파일/폴더")
            self.tree_preview_structure.setRootIsDecorated(True)

    def _apply_config_to_ui(self) -> None:
        """constants.json의 설정을 UI에 적용 (ComboBox 항목만)
        
        주의: GUI 기본값, 범위, 체크박스 상태는 모두 Designer에서 설정한 것을 사용
        """
        # ComboBox 항목 설정
        if hasattr(self, 'combo_rename_mode'):
            rename_modes = self.constants.get('rename_modes', {}).get('display', [])
            if self.combo_rename_mode.count() == 0 or [self.combo_rename_mode.itemText(i) for i in range(self.combo_rename_mode.count())] != rename_modes:
                current_text = self.combo_rename_mode.currentText()
                self.combo_rename_mode.clear()
                self.combo_rename_mode.addItems(rename_modes)
                if current_text and current_text in rename_modes:
                    self.combo_rename_mode.setCurrentText(current_text)
                elif rename_modes:
                    self.combo_rename_mode.setCurrentIndex(0)
        
        if hasattr(self, 'combo_output_mode'):
            output_modes = self.constants.get('output_modes', {}).get('display', [])
            if self.combo_output_mode.count() == 0 or [self.combo_output_mode.itemText(i) for i in range(self.combo_output_mode.count())] != output_modes:
                current_text = self.combo_output_mode.currentText()
                self.combo_output_mode.clear()
                self.combo_output_mode.addItems(output_modes)
                if current_text and current_text in output_modes:
                    self.combo_output_mode.setCurrentText(current_text)
                elif output_modes:
                    self.combo_output_mode.setCurrentIndex(0)
        
        if hasattr(self, 'combo_index_base'):
            index_base_options = self.constants.get('index_base_options', {}).get('display', [])
            if self.combo_index_base.count() == 0 or [self.combo_index_base.itemText(i) for i in range(self.combo_index_base.count())] != index_base_options:
                current_text = self.combo_index_base.currentText()
                self.combo_index_base.clear()
                self.combo_index_base.addItems(index_base_options)
                if current_text and current_text in index_base_options:
                    self.combo_index_base.setCurrentText(current_text)
                elif index_base_options:
                    self.combo_index_base.setCurrentIndex(0)
        
        # 참고: 
        # - GUI 기본값(prefix, postfix, pad_width, 체크박스 상태 등)은 Designer에서 설정
        # - 범위(min/max)도 Designer에서 설정
        # - constants.json은 GUI 표시값 <-> 메서드명 매핑만 포함

    def _connect(self) -> None:
        """시그널-슬롯 연결"""
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
        """폴더 선택 다이얼로그"""
        path = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if path:
            self.edit_folder.setText(path)

    def _validate(self) -> tuple[Path, str, str, int, int, float, int, str, str, bool, int, int, bool, bool, bool, Path | None, bool, bool, bool, bool] | None:
        """입력값 검증 및 GUI 값 -> 라이브러리 메서드명 매핑"""
        folder = Path(self.edit_folder.text().strip())
        pattern = self.edit_pattern.text().strip() or "*"
        
        # GUI 표시값을 라이브러리 메서드명으로 매핑
        rename_mode_display = self.combo_rename_mode.currentText()
        rename_method = self.constants.get('rename_modes', {}).get('mapping', {}).get(rename_mode_display, 'build_new_name')
        
        # index_base 매핑
        index_base_display = self.combo_index_base.currentText()
        index_base = self.constants.get('index_base_options', {}).get('mapping', {}).get(index_base_display, 1)
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
        preserve_folder_structure = self.chk_preserve_folder_structure.isChecked() if hasattr(self, 'chk_preserve_folder_structure') else True
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
            rename_method,  # 메서드명으로 변경
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
            preserve_folder_structure,
            dest_root,
            move,
            overwrite,
            dry_run,
            verbose,
        )

    def _start_worker(self, *, dry_run_override: bool | None = None) -> None:
        """Worker 시작"""
        validated = self._validate()
        if not validated:
            return

        (
            folder,
            pattern,
            rename_method,
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
            preserve_folder_structure,
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
        self.logger.info("User started renaming task: folder=%s, pattern=%s", folder, pattern)

        self.thread = QThread(self)
        self.worker = RenamerWorker(
            folder=folder,
            pattern=pattern,
            rename_method=rename_method,  # 메서드명 전달
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
            preserve_folder_structure=preserve_folder_structure,
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
        """미리보기 실행"""
        # 미리보기 트리 업데이트
        self._update_preview_tree()
        # 기존 미리보기 로직 실행
        self._start_worker(dry_run_override=True)

    @Slot()
    def _on_run(self) -> None:
        """실행"""
        self._start_worker(dry_run_override=None)

    @Slot(str)
    def _on_progress(self, text: str) -> None:
        """진행 로그 업데이트"""
        if text:
            self.log.appendPlainText(text.rstrip("\n"))

    @Slot(int, int)
    def _on_progress_update(self, current: int, total: int) -> None:
        """진행률 업데이트"""
        if total <= 0:
            self.progress.setRange(0, 0)
            return
        self.progress.setRange(0, total)
        self.progress.setValue(current)

    @Slot()
    def _on_clear_log(self) -> None:
        """로그 삭제"""
        self.log.clear()

    @Slot()
    def _on_browse_dst(self) -> None:
        """결과 폴더 선택 다이얼로그"""
        path = QFileDialog.getExistingDirectory(self, "결과 폴더 선택")
        if path:
            self.edit_dst.setText(path)

    def _update_output_mode(self) -> None:
        """출력 모드에 따른 UI 업데이트"""
        is_preserve = self.combo_output_mode.currentIndex() == 1
        self.dst_box.setEnabled(is_preserve)
        self.dst_box.setVisible(is_preserve)
        # 체크박스는 "다른 폴더" 모드일 때만 활성화
        if hasattr(self, 'chk_preserve_folder_structure'):
            self.chk_preserve_folder_structure.setEnabled(is_preserve)

    def _update_rename_mode(self) -> None:
        """이름 변경 모드에 따른 UI 업데이트"""
        rename_modes = self.constants.get('rename_modes', {}).get('display', [])
        is_new_rule = self.combo_rename_mode.currentText() == rename_modes[0] if rename_modes else True
        # 새로운 규칙으로 변경 시에만 인덱스 관련 컨트롤 활성화
        self.combo_index_base.setEnabled(is_new_rule)
        self.spin_pad.setEnabled(is_new_rule)
        self.spin_index_mul.setEnabled(is_new_rule)
        self.spin_index_offset.setEnabled(is_new_rule)
        self.chk_reset_per_folder.setEnabled(is_new_rule)

    # ---------- Scan & Tree Highlight ----------
    def _compute_pairs_for_ui(self, paths: list[Path]) -> list[tuple[Path, int]]:
        """UI용 pairs 계산"""
        index_base_display = self.combo_index_base.currentText()
        base = self.constants.get('index_base_options', {}).get('mapping', {}).get(index_base_display, 1)
        
        # 폴더별로 그룹화 (동일 폴더 내 인덱스 매핑 우선)
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
        if not self.chk_reset_per_folder.isChecked():
            # 폴더별로 먼저 처리하되, 인덱스는 연속적으로 유지
            current_index = base
            for key in sorted(groups.keys(), key=lambda s: s.lower()):
                group_paths = sorted(groups[key], key=natural_sort_key)
                for gp in group_paths:
                    pairs.append((gp, current_index))
                    current_index += 1
        else:
            # 폴더별로 인덱스 초기화
            for key in sorted(groups.keys(), key=lambda s: s.lower()):
                group_paths = sorted(groups[key], key=natural_sort_key)
                for idx, gp in enumerate(group_paths):
                    pairs.append((gp, idx + base))
        return pairs

    def _on_scan(self) -> None:
        """파일 스캔"""
        folder = Path(self.edit_folder.text().strip())
        pattern = self.edit_pattern.text().strip() or "*"
        if not folder.exists() or not folder.is_dir():
            QMessageBox.warning(self, "경고", "유효한 폴더를 선택하세요.")
            return
        paths = list_files(folder, pattern, recursive=True)
        self._populate_tree(paths)
        self._highlight_tree()
        self._populate_current_structure_tree(paths)

    def _populate_tree(self, paths: list[Path]) -> None:
        """트리 위젯에 파일 목록 표시"""
        self.tree.clear()
        folder = Path(self.edit_folder.text().strip())
        groups: dict[str, list[Path]] = {}
        for p in paths:
            try:
                rel_parent = p.parent.relative_to(folder)
            except Exception:
                rel_parent = Path("")
            key = str(rel_parent)
            groups.setdefault(key, []).append(p)
        
        # index_base 매핑
        index_base_display = self.combo_index_base.currentText()
        base = self.constants.get('index_base_options', {}).get('mapping', {}).get(index_base_display, 1)
        
        for key in sorted(groups.keys(), key=lambda s: s.lower()):
            parent_item = QTreeWidgetItem(["", key if key else ".", ""])
            self.tree.addTopLevelItem(parent_item)
            for idx, p in enumerate(sorted(groups[key], key=natural_sort_key)):
                i = idx + base
                child = QTreeWidgetItem([str(i), key if key else ".", p.name])
                child.setData(0, Qt.UserRole, i)
                child.setData(1, Qt.UserRole, str(p))
                parent_item.addChild(child)
            parent_item.setExpanded(True)

    def _highlight_tree(self) -> None:
        """트리 항목 하이라이트"""
        apply_sel = self.chk_apply_selection.isChecked()
        sel_off = int(self.spin_sel_offset.value())
        sel_div = int(self.spin_sel_div.value())
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
        """선택 규칙 변경 시 트리 업데이트"""
        if self.tree.topLevelItemCount() == 0:
            self._on_scan()
            return
        self._highlight_tree()
        self._update_preview_tree()
    
    def _populate_current_structure_tree(self, paths: list[Path]) -> None:
        """현재 폴더 구조를 트리로 표시"""
        if not hasattr(self, 'tree_current_structure'):
            return
        
        self.tree_current_structure.clear()
        folder = Path(self.edit_folder.text().strip())
        
        # 폴더 구조를 트리로 구성
        folder_tree: dict[str, dict] = {}
        file_tree: dict[str, list[Path]] = {}
        
        for p in paths:
            try:
                rel_path = p.relative_to(folder)
            except Exception:
                continue
            
            # 폴더 경로 분리
            parts = rel_path.parts
            if len(parts) == 1:
                # 루트에 있는 파일
                file_tree.setdefault("", []).append(p)
            else:
                # 하위 폴더에 있는 파일
                folder_path = "/".join(parts[:-1])
                file_tree.setdefault(folder_path, []).append(p)
                
                # 중간 폴더들 추가
                current_path = ""
                for part in parts[:-1]:
                    if current_path:
                        current_path = f"{current_path}/{part}"
                    else:
                        current_path = part
                    if current_path not in folder_tree:
                        folder_tree[current_path] = {}
        
        # 트리 아이템 생성
        def create_folder_item(folder_path: str, parent_item: QTreeWidgetItem | None = None) -> QTreeWidgetItem:
            """폴더 아이템 생성"""
            folder_name = folder_path.split("/")[-1] if "/" in folder_path else folder_path
            if parent_item:
                item = QTreeWidgetItem(parent_item, [folder_name])
            else:
                item = QTreeWidgetItem(self.tree_current_structure, [folder_name])
            item.setExpanded(True)
            return item
        
        # 루트 파일들 추가
        if "" in file_tree:
            root_item = QTreeWidgetItem(self.tree_current_structure, ["."])
            root_item.setExpanded(True)
            for p in sorted(file_tree[""], key=natural_sort_key):
                file_item = QTreeWidgetItem(root_item, [p.name])
        
        # 폴더별로 정렬하여 추가
        for folder_path in sorted(folder_tree.keys(), key=lambda s: s.lower()):
            parts = folder_path.split("/")
            parent_item = None
            current_path = ""
            
            for part in parts:
                if current_path:
                    current_path = f"{current_path}/{part}"
                else:
                    current_path = part
                
                # 이미 존재하는지 확인
                found = False
                if parent_item:
                    for i in range(parent_item.childCount()):
                        if parent_item.child(i).text(0) == part:
                            parent_item = parent_item.child(i)
                            found = True
                            break
                else:
                    for i in range(self.tree_current_structure.topLevelItemCount()):
                        if self.tree_current_structure.topLevelItem(i).text(0) == part:
                            parent_item = self.tree_current_structure.topLevelItem(i)
                            found = True
                            break
                
                if not found:
                    parent_item = create_folder_item(current_path, parent_item)
            
            # 해당 폴더의 파일들 추가
            if folder_path in file_tree:
                for p in sorted(file_tree[folder_path], key=natural_sort_key):
                    file_item = QTreeWidgetItem(parent_item, [p.name])
    
    def _update_preview_tree(self) -> None:
        """미리보기 트리 업데이트"""
        if not hasattr(self, 'tree_preview_structure'):
            return
        
        self.tree_preview_structure.clear()
        
        # 검증
        validated = self._validate()
        if not validated:
            return
        
        folder, pattern, rename_method, index_base, pad_width, index_mul, index_offset, prefix, postfix, apply_selection, sel_offset, sel_division, reset_per_folder, preserve_tree, preserve_folder_structure, dest_root, move, overwrite, dry_run, verbose = validated
        
        # 파일 목록 가져오기
        paths = list_files(folder, pattern, recursive=True)
        if not paths:
            return
        
        # pairs 계산
        pairs = self._compute_pairs_for_ui(paths)
        
        # 파일명 생성 함수 가져오기
        from tools.renamer.functions import build_new_name, build_keep_name
        if rename_method == "build_keep_name":
            build_func = build_keep_name
        else:
            build_func = build_new_name
        
        # 목적지 경로 계산
        preview_data: dict[str, list[tuple[str, str]]] = {}  # folder_path -> [(old_name, new_name)]
        
        for src, index_value in pairs:
            suffix = src.suffix
            
            if rename_method == "build_keep_name":
                new_name = build_func(src.stem, suffix, prefix, postfix)
            else:
                new_name = build_func(index_value, suffix, pad_width, index_mul, index_offset, prefix, postfix)
            
            # 목적지 경로 결정
            if preserve_tree and dest_root is not None:
                if preserve_folder_structure:
                    try:
                        rel_parent = src.parent.relative_to(folder)
                    except Exception:
                        rel_parent = Path("")
                    dest_folder = str(rel_parent).replace("\\", "/") if str(rel_parent) else "."
                else:
                    dest_folder = "."
            else:
                try:
                    rel_parent = src.parent.relative_to(folder)
                except Exception:
                    rel_parent = Path("")
                dest_folder = str(rel_parent).replace("\\", "/") if str(rel_parent) else "."
            
            preview_data.setdefault(dest_folder, []).append((src.name, new_name))
        
        # 트리 구성
        def create_preview_folder_item(folder_path: str, parent_item: QTreeWidgetItem | None = None) -> QTreeWidgetItem:
            """미리보기 폴더 아이템 생성"""
            if folder_path == ".":
                folder_name = dest_root.name if dest_root else "."
            else:
                folder_name = folder_path.split("/")[-1] if "/" in folder_path else folder_path
            
            if parent_item:
                item = QTreeWidgetItem(parent_item, [folder_name])
            else:
                item = QTreeWidgetItem(self.tree_preview_structure, [folder_name])
            item.setExpanded(True)
            return item
        
        # 루트 파일들 추가
        if "." in preview_data:
            root_name = dest_root.name if (preserve_tree and dest_root) else "."
            root_item = QTreeWidgetItem(self.tree_preview_structure, [root_name])
            root_item.setExpanded(True)
            for old_name, new_name in sorted(preview_data["."], key=lambda x: x[1]):
                file_item = QTreeWidgetItem(root_item, [new_name])
        
        # 폴더별로 정렬하여 추가
        for folder_path in sorted([f for f in preview_data.keys() if f != "."], key=lambda s: s.lower()):
            parts = folder_path.split("/")
            parent_item = None
            current_path = ""
            
            for part in parts:
                if current_path:
                    current_path = f"{current_path}/{part}"
                else:
                    current_path = part
                
                # 이미 존재하는지 확인
                found = False
                if parent_item:
                    for i in range(parent_item.childCount()):
                        if parent_item.child(i).text(0) == part:
                            parent_item = parent_item.child(i)
                            found = True
                            break
                else:
                    for i in range(self.tree_preview_structure.topLevelItemCount()):
                        if self.tree_preview_structure.topLevelItem(i).text(0) == part:
                            parent_item = self.tree_preview_structure.topLevelItem(i)
                            found = True
                            break
                
                if not found:
                    parent_item = create_preview_folder_item(current_path, parent_item)
            
            # 해당 폴더의 파일들 추가
            for old_name, new_name in sorted(preview_data[folder_path], key=lambda x: x[1]):
                file_item = QTreeWidgetItem(parent_item, [new_name])

    @Slot(int, int)
    def _on_finished(self, ok: int, total: int) -> None:
        """작업 완료"""
        msg = f"완료: {ok}/{total}"
        self.log.appendPlainText(msg)
        self.logger.info("Renaming task finished: %d/%d files processed", ok, total)
        self._cleanup_worker()
        self._set_running(False)

    @Slot(str)
    def _on_failed(self, msg: str) -> None:
        """작업 실패"""
        error_msg = f"오류: {msg}"
        self.log.appendPlainText(error_msg)
        self.logger.error("Renaming task failed: %s", msg)
        self._cleanup_worker()
        self._set_running(False)

    def _cleanup_worker(self) -> None:
        """Worker 정리"""
        if self.thread and self.worker:
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None

    def _set_running(self, running: bool) -> None:
        """실행 중 상태 설정"""
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
        ] + ([self.chk_preserve_folder_structure] if hasattr(self, 'chk_preserve_folder_structure') else []):
            w.setEnabled(not running)


def main() -> None:
    """독립 실행용 (테스트)"""
    app = QApplication(sys.argv)
    win = RenamerWindow()
    # Designer에서 설정한 윈도우 크기가 자동 적용됨
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
