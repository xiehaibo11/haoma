# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['FINAL_APP.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=['extractor'],
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
    name='LeisuPhoneExtractor_latest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\colly\\livestream-scraper\\desktop_app\\build\\NBF.ico'],
)
