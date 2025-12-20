"""업무 자동화 도구 모음"""
from __future__ import annotations

import sys
from typing import Protocol
from PySide6.QtWidgets import QWidget

from tools.common.log_utils import get_tool_logger


class ToolInfo:
    """도구 정보"""
    def __init__(
        self,
        name: str,
        description: str,
        icon: str | None = None,
    ):
        self.name = name
        self.description = description
        self.icon = icon


class BaseTool(Protocol):
    """도구 기본 인터페이스"""
    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        """도구의 GUI 위젯을 생성하여 반환"""
        ...


# 도구 등록 딕셔너리
_registered_tools: dict[str, tuple[ToolInfo, type[BaseTool]]] = {}


def register_tool(tool_id: str, tool_info: ToolInfo, tool_class: type[BaseTool]):
    """도구를 등록"""
    _registered_tools[tool_id] = (tool_info, tool_class)


def get_registered_tools() -> dict[str, ToolInfo]:
    """등록된 모든 도구 정보 반환"""
    return {tool_id: info for tool_id, (info, _) in _registered_tools.items()}


def create_tool_widget(tool_id: str, parent: QWidget | None = None) -> QWidget | None:
    """도구 ID로 GUI 위젯 생성"""
    logger = get_tool_logger("tools")
    logger.debug("create_tool_widget called: tool_id=%s, parent=%s", tool_id, parent)
    logger.debug("Registered tools: %s", list(_registered_tools.keys()))
    
    if tool_id not in _registered_tools:
        logger.error("Tool not found in registered tools: %s", tool_id)
        return None
    
    try:
        _, tool_class = _registered_tools[tool_id]
        logger.debug("Tool class: %s", tool_class)
        logger.debug("Instantiating tool class")
        tool_instance = tool_class()
        logger.debug("Tool instance created: %s", tool_instance)
        logger.debug("Calling create_widget(parent=%s)", parent)
        widget = tool_instance.create_widget(parent)
        logger.debug("create_widget returned: %s (type: %s)", widget, type(widget).__name__ if widget else None)
        return widget
    except Exception as e:
        logger.error("Exception while creating tool widget for %s: %s", tool_id, str(e), exc_info=True)
        raise


# 도구들을 자동으로 등록
def _register_all_tools():
    """모든 도구를 자동으로 등록"""
    logger = get_tool_logger("tools")
    logger.debug("Starting tool registration")
    logger.debug("sys.frozen: %s", getattr(sys, 'frozen', False))
    
    # renamer 도구 등록
    try:
        logger.debug("Attempting to import tools.renamer")
        from tools.renamer import RenamerTool, RENAMER_INFO
        logger.debug("Successfully imported RenamerTool and RENAMER_INFO")
        register_tool("renamer", RENAMER_INFO, RenamerTool)
        logger.info("Renamer tool registered successfully")
    except ImportError as e:
        logger.error("Failed to import renamer tool: %s", str(e), exc_info=True)
        # 도구가 없으면 무시
    except Exception as e:
        logger.error("Unexpected error while registering renamer tool: %s", str(e), exc_info=True)
    
    # folder_creator 도구 등록
    try:
        logger.debug("Attempting to import tools.folder_creator")
        from tools.folder_creator import FolderCreatorTool, FOLDER_CREATOR_INFO
        logger.debug("Successfully imported FolderCreatorTool and FOLDER_CREATOR_INFO")
        register_tool("folder_creator", FOLDER_CREATOR_INFO, FolderCreatorTool)
        logger.info("Folder Creator tool registered successfully")
    except ImportError as e:
        logger.error("Failed to import folder_creator tool: %s", str(e), exc_info=True)
        # 도구가 없으면 무시
    except Exception as e:
        logger.error("Unexpected error while registering folder_creator tool: %s", str(e), exc_info=True)


# 모듈 로드 시 자동 등록
_register_all_tools()

