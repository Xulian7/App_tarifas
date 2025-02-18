# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['gestion_db.py'],  # Archivo principal
    pathex=[],  
    binaries=[],  
    datas=[('diccionarios', 'diccionarios'), ('img', 'img')],  # Archivos de datos sin logica.py
    hiddenimports=[],  
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
    name='gestion_db',  
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Si tiene UI, mantener en False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
