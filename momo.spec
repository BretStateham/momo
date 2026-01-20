# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MoMo.

Build command:
    pyinstaller momo.spec

This creates a single executable with no console window.
"""

import sys
from pathlib import Path

# Get the source directory
src_path = Path('src')

a = Analysis(
    [str(src_path / 'main.py')],
    pathex=[str(src_path)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pystray._win32',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MoMo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available
)
