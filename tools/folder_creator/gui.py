#!/usr/bin/env python3
"""Folder Creator 도구의 GUI"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QThread, Slot
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QProgressBar,
    QPlainTextEdit,
)

from tools.common.log_utils import get_tool_logger
from tools.folder_creator.pipeline import FolderCreatorWorker


class FolderCreatorWindow(QMainWindow):
    """Folder Creator GUI"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.logger = get_tool_logger("folder_creator")
        self.constants = self._load_constants()
        self._load_ui()
        self._connect()

        self.thread: QThread | None = None
        self.worker: FolderCreatorWorker | None = None
        self.logger.info("FolderCreatorWindow initialized")

    def _load_constants(self) -> dict:
        """constants.json 로드"""
        config_path = Path(__file__).parent / 'constants.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_ui(self) -> None:
        """UI 위젯 직접 생성"""
        self.setWindowTitle("폴더 생성 도구")
        self.setGeometry(100, 100, 600, 500)
        
        # 중앙 위젯 생성
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃 (수직)
        main_layout = QVBoxLayout(central_widget)
        
        # 폼 레이아웃 생성
        form_layout = QFormLayout()
        
        # 부모 폴더
        label_parent_path = QLabel("부모 폴더")
        parent_path_layout = QHBoxLayout()
        self.edit_parent_path = QLineEdit()
        self.btn_browse = QPushButton("폴더 선택")
        parent_path_layout.addWidget(self.edit_parent_path)
        parent_path_layout.addWidget(self.btn_browse)
        form_layout.addRow(label_parent_path, parent_path_layout)
        
        # 폴더 개수
        label_count = QLabel("폴더 개수")
        self.spin_count = QSpinBox()
        self.spin_count.setMinimum(1)
        self.spin_count.setMaximum(10000)
        self.spin_count.setValue(20)
        form_layout.addRow(label_count, self.spin_count)
        
        # Prefix
        label_prefix = QLabel("Prefix")
        self.edit_prefix = QLineEdit()
        self.edit_prefix.setText("test")
        form_layout.addRow(label_prefix, self.edit_prefix)
        
        # Suffix
        label_suffix = QLabel("Suffix")
        self.edit_suffix = QLineEdit()
        self.edit_suffix.setText("bseong")
        form_layout.addRow(label_suffix, self.edit_suffix)
        
        # 패딩 너비
        label_padding = QLabel("패딩 너비")
        self.spin_padding = QSpinBox()
        self.spin_padding.setMinimum(1)
        self.spin_padding.setMaximum(10)
        self.spin_padding.setValue(4)
        form_layout.addRow(label_padding, self.spin_padding)
        
        # 시작 인덱스
        label_start_index = QLabel("시작 인덱스")
        self.spin_start_index = QSpinBox()
        self.spin_start_index.setMinimum(0)
        self.spin_start_index.setMaximum(100000)
        self.spin_start_index.setValue(1)
        form_layout.addRow(label_start_index, self.spin_start_index)
        
        main_layout.addLayout(form_layout)
        
        # 실행 버튼
        self.btn_run = QPushButton("폴더 생성")
        main_layout.addWidget(self.btn_run)
        
        # 진행률 표시
        self.progress = QProgressBar()
        self.progress.setValue(0)
        main_layout.addWidget(self.progress)
        
        # 로그 레이아웃
        log_layout = QHBoxLayout()
        label_log = QLabel("로그")
        self.btn_clear_log = QPushButton("로그 삭제")
        log_layout.addWidget(label_log)
        log_layout.addStretch()
        log_layout.addWidget(self.btn_clear_log)
        main_layout.addLayout(log_layout)
        
        # 로그 텍스트 영역
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        main_layout.addWidget(self.log)

    def _connect(self) -> None:
        """시그널-슬롯 연결"""
        self.btn_browse.clicked.connect(self._on_browse)
        self.btn_run.clicked.connect(self._on_run)
        self.btn_clear_log.clicked.connect(self._on_clear_log)

    @Slot()
    def _on_browse(self) -> None:
        """폴더 선택 다이얼로그"""
        path = QFileDialog.getExistingDirectory(self, "부모 폴더 선택")
        if path:
            self.edit_parent_path.setText(path)

    def _validate(self) -> tuple[Path, int, str, str, int, int] | None:
        """입력값 검증"""
        parent_path = Path(self.edit_parent_path.text().strip())
        count = self.spin_count.value()
        prefix = self.edit_prefix.text().strip()
        suffix = self.edit_suffix.text().strip()
        padding = self.spin_padding.value()
        start_index = self.spin_start_index.value()

        if not parent_path.parent.exists() and not parent_path.exists():
            QMessageBox.warning(self, "경고", "유효한 부모 폴더 경로를 입력하세요.")
            return None

        if count <= 0:
            QMessageBox.warning(self, "경고", "폴더 개수는 1 이상이어야 합니다.")
            return None

        if not prefix:
            QMessageBox.warning(self, "경고", "Prefix를 입력하세요.")
            return None

        if not suffix:
            QMessageBox.warning(self, "경고", "Suffix를 입력하세요.")
            return None

        return (parent_path, count, prefix, suffix, padding, start_index)

    def _start_worker(self) -> None:
        """Worker 시작"""
        validated = self._validate()
        if not validated:
            return

        parent_path, count, prefix, suffix, padding, start_index = validated

        self._set_running(True)
        self.log.appendPlainText("작업 시작...")
        self.logger.info("User started folder creation task: parent=%s, count=%d", parent_path, count)

        self.thread = QThread(self)
        self.worker = FolderCreatorWorker(
            parent_path=parent_path,
            count=count,
            prefix=prefix,
            suffix=suffix,
            padding=padding,
            start_index=start_index,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progressed.connect(self._on_progress)
        self.worker.progress.connect(self._on_progress_update)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.thread.start()

    @Slot()
    def _on_run(self) -> None:
        """실행"""
        self._start_worker()

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

    @Slot(int)
    def _on_finished(self, count: int) -> None:
        """작업 완료"""
        msg = f"완료: {count}개 폴더 생성됨"
        self.log.appendPlainText(msg)
        self.logger.info("Task completed: %d folders created", count)
        self._cleanup_worker()
        self._set_running(False)
        QMessageBox.information(self, "완료", msg)

    @Slot(str)
    def _on_failed(self, msg: str) -> None:
        """작업 실패"""
        error_msg = f"오류: {msg}"
        self.log.appendPlainText(error_msg)
        self.logger.error("Task failed: %s", msg)
        self._cleanup_worker()
        self._set_running(False)
        QMessageBox.critical(self, "오류", error_msg)

    def _cleanup_worker(self) -> None:
        """Worker 정리"""
        if self.thread and self.worker:
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None

    def _set_running(self, running: bool) -> None:
        """실행 중 상태 설정"""
        widgets = [
            self.edit_parent_path,
            self.btn_browse,
            self.spin_count,
            self.edit_prefix,
            self.edit_suffix,
            self.spin_padding,
            self.spin_start_index,
            self.btn_run,
        ]
        for w in widgets:
            w.setEnabled(not running)


def main() -> None:
    """독립 실행용 (테스트)"""
    app = QApplication(sys.argv)
    win = FolderCreatorWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

