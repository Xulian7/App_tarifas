# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_app.py'],  # Archivo principal de la aplicación
    pathex=['.'],  # Asegura que PyInstaller busque en el directorio actual
    binaries=[],  # No se agregan binarios directamente
    datas=[
        # Agregar datos adicionales como diccionarios, imágenes, scripts adicionales
        ('diccionarios', 'diccionarios'),
        ('img', 'img'),
        ('logica.py', '.'),  # Si tienes un archivo logica.py, también se incluye
        # Asegúrate de incluir tesseract.exe en los datos
        ('C:/Program Files/Tesseract-OCR/tesseract.exe', 'tesseract.exe'),
    ],
    hiddenimports=[],  # Si hay módulos ocultos, agréguelos aquí
    hookspath=[],  # Ruta de hooks adicionales si es necesario
    runtime_hooks=[],  # Hooks en tiempo de ejecución
    excludes=[],  # Excluye módulos no necesarios
    noarchive=False
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main_app',  # Nombre del ejecutable
    debug=False,
    strip=False,
    upx=True,
    console=False,  # Cambia a False si no quieres que se abra la terminal
    icon='icono.ico'  # Icono de la aplicación
)

