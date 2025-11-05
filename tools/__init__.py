"""업무 자동화 도구 모음"""
from __future__ import annotations

from typing import Protocol
from PySide6.QtWidgets import QWidget


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
    if tool_id not in _registered_tools:
        return None
    _, tool_class = _registered_tools[tool_id]
    return tool_class().create_widget(parent)


# 도구들을 자동으로 등록
def _register_all_tools():
    """모든 도구를 자동으로 등록"""
    # renamer 도구 등록
    try:
        from tools.renamer import RenamerTool, RENAMER_INFO
        register_tool("renamer", RENAMER_INFO, RenamerTool)
    except ImportError:
        pass  # 도구가 없으면 무시


# 모듈 로드 시 자동 등록
_register_all_tools()

