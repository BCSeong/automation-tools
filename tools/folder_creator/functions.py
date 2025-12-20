"""Folder Creator 도구 전용 함수들"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

# 직접 실행 시 프로젝트 루트를 sys.path에 추가
if __name__ == "__main__" or (len(sys.argv) > 0 and Path(sys.argv[0]).name == Path(__file__).name):
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

try:
    from tools.common.log_utils import get_tool_logger
except ImportError:
    # 직접 실행 시 import 실패하면 sys.path 조작 후 재시도
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from tools.common.log_utils import get_tool_logger

logger = get_tool_logger("folder_creator")


def create_folders(
    parent_path: str | Path,
    count: int,
    prefix: str,
    suffix: str,
    padding: int = 4,
    start_index: int = 1,
) -> List[Path]:
    """특정 규칙을 가진 폴더들을 생성
    
    Args:
        parent_path: 부모 폴더 경로
        count: 생성할 폴더 개수
        prefix: 폴더명 prefix (예: "test")
        suffix: 폴더명 suffix (예: "bseong")
        padding: 숫자 패딩 너비 (기본값: 4)
        start_index: 시작 인덱스 (기본값: 1)
        
    Returns:
        생성된 폴더 경로 리스트
        
    Example:
        >>> create_folders("/path/to/parent", 20, "test", "bseong", 4, 1)
        [Path("/path/to/parent/test_0001_bseong"), ...]
    """
    parent = Path(parent_path)
    
    # 부모 폴더가 없으면 생성
    if not parent.exists():
        logger.debug("Creating parent directory: %s", parent)
        parent.mkdir(parents=True, exist_ok=True)
    
    created_folders = []
    
    for i in range(count):
        index = start_index + i
        num_str = f"{index:0{padding}d}"
        
        # 폴더명 생성: prefix_num_suffix
        folder_name = f"{prefix}_{num_str}_{suffix}"
        folder_path = parent / folder_name
        
        # 폴더 생성
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.debug("Created folder: %s", folder_path)
        else:
            logger.warning("Folder already exists: %s", folder_path)
        
        created_folders.append(folder_path)
    
    logger.info("Created %d folders in %s", len(created_folders), parent)
    return created_folders


# CLI 테스트 지원
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Folder Creator 함수 테스트")
    parser.add_argument('--parent-path', type=str, required=True, help='부모 폴더 경로')
    parser.add_argument('--count', type=int, required=True, help='생성할 폴더 개수')
    parser.add_argument('--prefix', type=str, default='test', help='폴더명 prefix')
    parser.add_argument('--suffix', type=str, default='bseong', help='폴더명 suffix')
    parser.add_argument('--padding', type=int, default=4, help='숫자 패딩 너비')
    parser.add_argument('--start-index', type=int, default=1, help='시작 인덱스')
    
    args = parser.parse_args()
    
    result = create_folders(
        args.parent_path,
        args.count,
        args.prefix,
        args.suffix,
        args.padding,
        args.start_index,
    )
    
    print(f"Created {len(result)} folders:")
    for folder in result:
        print(f"  {folder}")

