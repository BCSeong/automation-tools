"""파일명 일괄 변경 도구"""
from __future__ import annotations

from tools import ToolInfo
from tools.renamer.gui import RenamerWindow

__all__ = ["RenamerTool", "RENAMER_INFO"]


RENAMER_INFO = ToolInfo(
    name="파일명 변경 도구",
    description="이미지 파일명을 일괄적으로 변경하는 도구",
    icon=None,
)


class RenamerTool:
    """Renamer 도구 클래스"""
    
    def create_widget(self, parent=None):
        """Renamer GUI 윈도우 생성"""
        window = RenamerWindow(parent)
        # Designer에서 설정한 윈도우 크기가 자동 적용됨
        return window

