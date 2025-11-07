"""UI 관련 범용 함수"""
from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QHeaderView, QTreeWidgetItem
from PySide6.QtUiTools import QUiLoader


def load_ui_file(ui_path: Path | str, target_window: QMainWindow) -> None:
    """Designer .ui 파일을 로드하여 QMainWindow에 적용
    
    이 함수는 Designer로 만든 .ui 파일을 로드하고,
    Designer에서 설정한 objectName으로 정의된 모든 위젯을
    target_window 인스턴스에 자동으로 연결합니다.
    
    Args:
        ui_path: .ui 파일 경로
        target_window: UI를 적용할 QMainWindow 인스턴스
        
    Example:
        >>> class MyWindow(QMainWindow):
        ...     def __init__(self):
        ...         super().__init__()
        ...         load_ui_file(Path(__file__).parent / 'ui' / 'main.ui', self)
        ...         # 이제 Designer에서 설정한 objectName으로 위젯 접근 가능
        ...         # 예: self.btn_run.clicked.connect(...)
    """
    ui_path = Path(ui_path)
    if not ui_path.exists():
        raise FileNotFoundError(f"UI file not found: {ui_path}")
    
    loader = QUiLoader()
    # 경로 문자열을 직접 전달
    widget = loader.load(str(ui_path), target_window)
    
    if widget is None:
        raise RuntimeError(f"Failed to load UI file: {ui_path}")
    
    # QUiLoader는 새 위젯을 반환하므로, 위젯의 속성들을 현재 윈도우에 복사
    # .ui 파일의 최상위가 QMainWindow인 경우, centralWidget을 가져옴
    if hasattr(widget, 'centralWidget'):
        central = widget.centralWidget()
        if central:
            # 기존 centralWidget 제거 후 새로 설정
            old_central = target_window.centralWidget()
            if old_central:
                old_central.setParent(None)
            target_window.setCentralWidget(central)
            central.setParent(target_window)
    
    # 위젯의 모든 속성을 현재 윈도우에 복사 (objectName으로 접근 가능하도록)
    # 이렇게 하면 Designer에서 설정한 objectName으로 직접 접근 가능
    for attr_name in dir(widget):
        if not attr_name.startswith('_') and hasattr(widget, attr_name):
            try:
                attr_value = getattr(widget, attr_name)
                # 위젯인 경우에만 복사 (메서드나 시그널은 제외)
                if isinstance(attr_value, (QWidget, QHeaderView, QTreeWidgetItem)):
                    setattr(target_window, attr_name, attr_value)
            except Exception:
                pass

