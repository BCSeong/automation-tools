# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 빌드 설정 파일
cmd로 현재 경로 진입, 아래 커맨드 입력
> pyinstaller build.spec
"""
from __future__ import annotations

import glob
from pathlib import Path

block_cipher = None


def collect_tool_datas() -> list[tuple[str, str]]:
    """tools/* 하위의 ui 및 constants 데이터를 PyInstaller용으로 수집"""
    datas: list[tuple[str, str]] = []
    patterns = [
        'tools/*/ui/*.ui',
        'tools/*/constants.json',
    ]

    for pattern in patterns:
        for src_path in glob.glob(pattern, recursive=False):
            src = Path(src_path)
            # dist 내부에서도 동일한 폴더 구조 유지 (tools/...)
            dest = str(src.parent)
            datas.append((str(src), dest))

    return datas


tool_datas = collect_tool_datas()

a = Analysis(
    ['main_gui.py'],
    pathex=[],
    binaries=[],
    datas=tool_datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtUiTools',
        'tools',
        'tools.common',
        'tools.common.file_utils',
        'tools.common.path_utils',
        'tools.common.ui_utils',
        'tools.common.log_utils',
        'tools.renamer',
        'tools.renamer.gui',
        'tools.renamer.pipeline',
        'tools.renamer.functions',
        'tools.folder_creator',
        'tools.folder_creator.gui',
        'tools.folder_creator.pipeline',
        'tools.folder_creator.functions',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='automation-tools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 애플리케이션이므로 콘솔 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일이 있으면 경로 지정
)

