"""경로 관련 범용 함수"""
from __future__ import annotations

from pathlib import Path
import re


def natural_sort_key(path: Path) -> list:
    """자연스러운 정렬을 위한 키 생성 (범용 함수)
    
    Args:
        path: 정렬할 경로
        
    Returns:
        정렬 키 리스트
        
    Example:
        >>> paths = [Path("file10.txt"), Path("file2.txt"), Path("file1.txt")]
        >>> sorted(paths, key=natural_sort_key)
        [Path("file1.txt"), Path("file2.txt"), Path("file10.txt")]
    """
    name = path.name
    tok = re.split(r"(\d+)", name)
    key = []
    for t in tok:
        key.append(int(t) if t.isdigit() else t.lower())
    return key

