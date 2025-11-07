# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 빌드 설정 파일
cmd로 현재 경로 진입, 아래 커맨드 입력
> pyinstaller build.spec
"""

block_cipher = None

a = Analysis(
    ['main_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # .ui 파일 포함 (Designer로 만든 UI 파일)
        ('tools/*/ui/*.ui', 'tools'),
        # constants.json 파일 포함
        ('tools/*/constants.json', 'tools'),
    ],
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

