"""파일 관련 범용 함수"""
from __future__ import annotations

from pathlib import Path
import shutil


def list_files(folder: Path, pattern: str, recursive: bool = True) -> list[Path]:
    """파일 목록 반환 (범용 함수)
    
    Args:
        folder: 검색할 폴더
        pattern: 파일 패턴 (예: "*.bmp", "*.txt")
        recursive: 하위 폴더까지 재귀적으로 검색할지 여부
        
    Returns:
        정렬된 파일 경로 리스트 (자연스러운 정렬)
        
    Example:
        >>> folder = Path("/path/to/folder")
        >>> files = list_files(folder, "*.bmp")
    """
    from tools.common.path_utils import natural_sort_key
    
    if recursive:
        paths = [p for p in folder.rglob(pattern) if p.is_file()]
    else:
        paths = [p for p in folder.glob(pattern) if p.is_file()]
    return sorted(paths, key=natural_sort_key)


def ensure_write(
    src: Path,
    dst: Path,
    *,
    move: bool = False,
    overwrite: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """파일 쓰기 처리 (복사/이동) - 범용 함수
    
    Args:
        src: 원본 파일 경로
        dst: 대상 파일 경로
        move: True면 이동, False면 복사
        overwrite: True면 기존 파일 덮어쓰기
        dry_run: True면 실제 작업 없이 로그만 출력
        verbose: True면 상세한 로그 출력
        
    Example:
        >>> src = Path("source.txt")
        >>> dst = Path("destination.txt")
        >>> ensure_write(src, dst, move=True, overwrite=True)
    """
    if dst.exists():
        if overwrite:
            if verbose:
                print(f"[overwrite] {dst}")
            if not dry_run and dst.is_file():
                dst.unlink()
        else:
            if verbose:
                print(f"[skip] 대상 파일 이미 존재: {dst}")
            return
    
    if verbose:
        action = "move" if move else "copy"
        print(f"[{action}] {src.name} -> {dst.name}")
    
    if dry_run:
        return
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    if move:
        # cross-device 이동 지원
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(src, dst)

