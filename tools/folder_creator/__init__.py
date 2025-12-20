"""폴더 생성 도구"""
from __future__ import annotations

from tools import ToolInfo
from tools.common.log_utils import get_tool_logger

__all__ = ["FolderCreatorTool", "FOLDER_CREATOR_INFO"]

logger = get_tool_logger("folder_creator")

FOLDER_CREATOR_INFO = ToolInfo(
    name="폴더 생성 도구",
    description="특정 규칙을 가진 폴더들을 일괄 생성하는 도구",
    icon=None,
)

logger.debug("FOLDER_CREATOR_INFO created for tool_id=%s", "folder_creator")


class FolderCreatorTool:
    """Folder Creator 도구 클래스"""
    
    def __init__(self):
        logger.debug("FolderCreatorTool instance created")
    
    def create_widget(self, parent=None):
        """Folder Creator GUI 윈도우 생성"""
        logger.debug("create_widget called: parent=%s", parent)
        try:
            logger.debug("Importing FolderCreatorWindow")
            from tools.folder_creator.gui import FolderCreatorWindow
            logger.debug("FolderCreatorWindow imported successfully")
            logger.debug("Creating FolderCreatorWindow instance")
            window = FolderCreatorWindow(parent)
            logger.debug("FolderCreatorWindow created: %s", window)
            return window
        except Exception as e:
            logger.error("Exception in create_widget: %s", str(e), exc_info=True)
            raise

