"""Renamer 도구 전용 함수들"""
from __future__ import annotations

from pathlib import Path

# Windows 파일명에 사용 불가 문자
INVALID_FILENAME_CHARS = set('\\/:*?"<>|')
MAX_FILENAME_LEN = 255


def build_parent_folder_prefix(rel_parent: Path) -> str:
    """상대 경로를 prefix 문자열로 변환 (grandparent_parent 형태).
    
    Args:
        rel_parent: 선택 폴더 기준 상대 부모 경로 (빈 Path면 루트)
    Returns:
        빈 문자열 또는 "part1_part2_..." 형태
    """
    if rel_parent is None or str(rel_parent).strip() in ("", "."):
        return ""
    parts = [p for p in rel_parent.parts if p.strip()]
    return "_".join(parts) if parts else ""


def validate_parent_folder_prefix(rel_parent: Path, new_name: str) -> tuple[bool, str]:
    """상위 폴더 prefix가 파일명에 사용 가능한지 검사.
    
    Returns:
        (True, "") 또는 (False, "에러 메시지")
    """
    prefix = build_parent_folder_prefix(rel_parent)
    if not prefix:
        if len(new_name) > MAX_FILENAME_LEN:
            return False, f"파일명이 너무 깁니다 ({len(new_name)}자). {MAX_FILENAME_LEN}자 이하여야 합니다."
        return True, ""
    
    for part in rel_parent.parts:
        for c in INVALID_FILENAME_CHARS:
            if c in part:
                return False, f"폴더 이름에 사용할 수 없는 문자가 포함되어 있습니다: '{part}' (문자 '{c}')"
        if not part.strip():
            return False, "폴더 이름이 비어 있을 수 없습니다."
    
    full_name = f"{prefix}_{new_name}"
    if len(full_name) > MAX_FILENAME_LEN:
        return False, (
            f"상위 폴더 prefix를 적용한 파일명이 너무 깁니다 ({len(full_name)}자). "
            f"{MAX_FILENAME_LEN}자 이하여야 합니다."
        )
    return True, ""


def build_new_name(
    index_value: int,
    suffix: str,
    pad_width: int,
    index_mul: float,
    index_offset: int,
    prefix: str,
    postfix: str,
) -> str:
    """새로운 규칙으로 파일명 생성
    
    Args:
        index_value: 인덱스 값
        suffix: 파일 확장자 (예: ".bmp")
        pad_width: 숫자 패딩 너비
        index_mul: 인덱스 곱셈 계수
        index_offset: 인덱스 오프셋
        prefix: 파일명 prefix
        postfix: 파일명 postfix
        
    Returns:
        생성된 파일명
        
    Example:
        >>> build_new_name(1, ".bmp", 4, 1.0, 0, "frame", "")
        "frame_0001.bmp"
    """
    mul = 0.0 if index_mul is None else float(index_mul)
    off = 0 if index_offset is None else index_offset
    computed_float = index_value * mul + off
    computed = int(round(computed_float))
    
    if pad_width is None or pad_width < 0:
        pad_width = 0
    
    if pad_width == 0:
        num_str = f"{computed}"
    else:
        num_str = f"{computed:0{pad_width}d}"

    px = (prefix or "").strip()
    if px:
        sep = "" if px.endswith(("_", "-")) else "_"
        base = f"{px}{sep}{num_str}"
    else:
        base = num_str

    post = (postfix or "").strip()
    if post:
        sep2 = "" if post.startswith(("_", "-")) else "_"
        base = f"{base}{sep2}{post}"

    return f"{base}{suffix}"


def build_keep_name(original_stem: str, suffix: str, prefix: str, postfix: str) -> str:
    """원본 파일명을 유지하면서 prefix와 postfix를 추가
    
    Args:
        original_stem: 원본 파일명 (확장자 제외)
        suffix: 파일 확장자 (예: ".bmp")
        prefix: 파일명 prefix
        postfix: 파일명 postfix
        
    Returns:
        생성된 파일명
        
    Example:
        >>> build_keep_name("original_file", ".bmp", "pre_", "_post")
        "pre_original_file_post.bmp"
    """
    px = (prefix or "").strip()
    post = (postfix or "").strip()
    
    # prefix 추가
    if px:
        sep = "" if px.endswith(("_", "-")) else "_"
        base = f"{px}{sep}{original_stem}"
    else:
        base = original_stem
    
    # postfix 추가
    if post:
        sep2 = "" if post.startswith(("_", "-")) else "_"
        base = f"{base}{sep2}{post}"
    
    return f"{base}{suffix}"


# CLI 테스트 지원
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Renamer 함수 테스트")
    parser.add_argument('--test', type=str, choices=['build_new_name', 'build_keep_name'], 
                        required=True, help='테스트할 함수')
    parser.add_argument('--index-value', type=int, default=1, help='인덱스 값 (build_new_name용)')
    parser.add_argument('--suffix', type=str, default='.bmp', help='파일 확장자')
    parser.add_argument('--pad-width', type=int, default=4, help='숫자 패딩 너비')
    parser.add_argument('--index-mul', type=float, default=1.0, help='인덱스 곱셈')
    parser.add_argument('--index-offset', type=int, default=0, help='인덱스 오프셋')
    parser.add_argument('--prefix', type=str, default='frame', help='파일명 prefix')
    parser.add_argument('--postfix', type=str, default='', help='파일명 postfix')
    parser.add_argument('--original-stem', type=str, default='test_file', help='원본 파일명 (build_keep_name용)')
    
    args = parser.parse_args()
    
    if args.test == 'build_new_name':
        result = build_new_name(
            args.index_value,
            args.suffix,
            args.pad_width,
            args.index_mul,
            args.index_offset,
            args.prefix,
            args.postfix,
        )
        print(f"build_new_name 결과: {result}")
        print(f"  입력: index={args.index_value}, suffix={args.suffix}, pad={args.pad_width}, "
              f"mul={args.index_mul}, offset={args.index_offset}, prefix={args.prefix}, postfix={args.postfix}")
    
    elif args.test == 'build_keep_name':
        result = build_keep_name(
            args.original_stem,
            args.suffix,
            args.prefix,
            args.postfix,
        )
        print(f"build_keep_name 결과: {result}")
        print(f"  입력: stem={args.original_stem}, suffix={args.suffix}, prefix={args.prefix}, postfix={args.postfix}")
