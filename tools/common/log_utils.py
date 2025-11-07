"""로깅 관련 범용 함수"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_log_directory() -> Path:
    """로그 파일 저장 디렉토리 반환
    
    저장 위치 우선순위:
    1. EXE 모드 (프로세스가 .exe로 실행 중): 실행 파일과 같은 디렉토리/logs/
    2. 개발 모드: 프로젝트 루트/logs/
    
    Returns:
        로그 디렉토리 경로
    """
    if getattr(sys, 'frozen', False):
        # EXE 모드: 실행 파일과 같은 디렉토리
        base_dir = Path(sys.executable).parent
    else:
        # 개발 모드: 프로젝트 루트 찾기
        # tools/common/log_utils.py -> automation-tools/
        base_dir = Path(__file__).parent.parent.parent
    
    log_dir = base_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger(
    name: str,
    log_file: Optional[str | Path] = None,
    level: int = logging.DEBUG,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """로거 설정 및 반환
    
    Args:
        name: 로거 이름 (보통 __name__ 또는 모듈명)
        log_file: 로그 파일명 (None이면 자동 생성)
        level: 로그 레벨 (기본값: logging.INFO)
        format_string: 로그 포맷 문자열 (None이면 기본 포맷 사용)
        
    Returns:
        설정된 로거 객체
        
    Example:
        >>> logger = setup_logger(__name__, "my_tool.log")
        >>> logger.info("작업 시작")
        >>> logger.error("오류 발생: %s", error_message)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 이미 핸들러가 있으면 추가하지 않음 (중복 방지)
    if logger.handlers:
        return logger
    
    # 기본 포맷
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string, datefmt='%Y-%m-%d %H:%M:%S')
    
    # 콘솔 핸들러 (개발 모드에서 유용)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (로그 파일 저장)
    if log_file is None:
        # 모든 로거가 동일한 로그 파일을 사용하도록 통합
        timestamp = datetime.now().strftime('%Y-%m-%d')
        log_dir = get_log_directory()
        log_file = log_dir / f"{timestamp}_automation-tools.log"
    else:
        log_file = Path(log_file)
        if not log_file.is_absolute():
            # 상대 경로인 경우 로그 디렉토리 기준
            log_dir = get_log_directory()
            log_file = log_dir / log_file
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_tool_logger(tool_name: str, level: int = logging.DEBUG) -> logging.Logger:
    """도구별 로거 생성 (간편 함수)
    
    Args:
        tool_name: 도구 이름 (예: "renamer")
        level: 로그 레벨 (기본값: logging.INFO)
        
    Returns:
        설정된 로거 객체
        
    Example:
        >>> logger = get_tool_logger("renamer")
        >>> logger.info("파일명 변경 작업 시작")
    """
    return setup_logger(
        name=f"tools.{tool_name}",
        log_file=None,  # 자동 생성
        level=level,
    )

