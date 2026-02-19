# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_data_files

crypt = collect_all('cryptography')
mydemands_datas = collect_data_files('mydemands')


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=crypt[1],
    datas=crypt[0] + mydemands_datas,
    hiddenimports=["huggingface_hub", "bcrypt", "mydemands.resources_rc", *crypt[2], "cryptography.hazmat.bindings._rust", "cryptography.hazmat.primitives.ciphers.aead"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
