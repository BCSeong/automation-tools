#!/usr/bin/env python3
"""업무 자동화 도구 메인 GUI"""
from __future__ import annotations

import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QGridLayout,
)
from PySide6.QtCore import Qt

import tools


class MainWindow(QMainWindow):
    """메인 GUI - 모든 도구를 선택할 수 있는 홈 화면"""
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("업무 자동화 도구")
        self._open_windows: list[QWidget] = []  # 열린 도구 윈도우 추적
        self._build_ui()
    
    def _build_ui(self) -> None:
        """UI 구성"""
        central = QWidget(self)
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        
        # 제목
        title = QLabel("업무 자동화 도구")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # 설명
        description = QLabel("사용할 도구를 선택하세요")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 20px;")
        layout.addWidget(description)
        
        # 도구 목록 영역 (스크롤 가능)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        tools_widget = QWidget()
        tools_layout = QGridLayout(tools_widget)
        tools_layout.setSpacing(15)
        
        # 등록된 도구들을 버튼으로 표시
        registered_tools = tools.get_registered_tools()
        
        row = 0  # row 초기화 (도구가 없을 때를 대비)
        col = 0
        cols_per_row = 3  # 한 줄에 3개씩 배치
        
        if not registered_tools:
            no_tools_label = QLabel("등록된 도구가 없습니다.")
            no_tools_label.setAlignment(Qt.AlignCenter)
            tools_layout.addWidget(no_tools_label, 0, 0)
        else:
            for tool_id, tool_info in registered_tools.items():
                btn = self._create_tool_button(tool_id, tool_info)
                tools_layout.addWidget(btn, row, col)
                
                col += 1
                if col >= cols_per_row:
                    col = 0
                    row += 1
        
        tools_layout.setRowStretch(row + 1, 1)
        tools_widget.setLayout(tools_layout)
        scroll.setWidget(tools_widget)
        
        layout.addWidget(scroll, 1)
    
    def _create_tool_button(self, tool_id: str, tool_info: tools.ToolInfo) -> QPushButton:
        """도구 버튼 생성"""
        btn = QPushButton()
        btn.setText(f"{tool_info.name}\n\n{tool_info.description}")
        btn.setMinimumHeight(120)
        btn.setMinimumWidth(200)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 15px;
                text-align: center;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        def on_click():
            self._open_tool(tool_id)
        
        btn.clicked.connect(on_click)
        return btn
    
    def _open_tool(self, tool_id: str) -> None:
        """도구 GUI를 팝업으로 열기"""
        widget = tools.create_tool_widget(tool_id, self)
        if widget is None:
            return
        
        # QMainWindow인 경우 show() 호출
        if isinstance(widget, QMainWindow):
            widget.show()
            self._open_windows.append(widget)
        else:
            # QWidget인 경우 QMainWindow로 감싸서 표시
            window = QMainWindow(self)
            window.setWindowTitle(widget.windowTitle() if hasattr(widget, 'windowTitle') else tool_id)
            window.setCentralWidget(widget)
            window.resize(800, 600)
            window.show()
            self._open_windows.append(window)


def main() -> None:
    """메인 함수"""
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

