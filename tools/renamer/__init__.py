"""파일명 일괄 변경 도구"""
from __future__ import annotations

from tools import ToolInfo
from tools.common.log_utils import get_tool_logger

__all__ = ["RenamerTool", "RENAMER_INFO"]

logger = get_tool_logger("renamer")

RENAMER_INFO = ToolInfo(
    name="파일명 변경 도구",
    description="이미지 파일명을 일괄적으로 변경하는 도구",
    icon=None,
)

logger.debug("RENAMER_INFO created for tool_id=%s", "renamer")


class RenamerTool:
    """Renamer 도구 클래스"""
    
    def __init__(self):
        logger.debug("RenamerTool instance created")
    
    def create_widget(self, parent=None):
        """Renamer GUI 윈도우 생성"""
        logger.debug("create_widget called: parent=%s", parent)
        try:
            logger.debug("Importing RenamerWindow")
            from tools.renamer.gui import RenamerWindow
            logger.debug("RenamerWindow imported successfully")
            logger.debug("Creating RenamerWindow instance")
            window = RenamerWindow(parent)
            logger.debug("RenamerWindow created: %s", window)
            # Designer에서 설정한 윈도우 크기가 자동 적용됨
            return window
        except Exception as e:
            logger.error("Exception in create_widget: %s", str(e), exc_info=True)
            raise

