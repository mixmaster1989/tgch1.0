import PyInstaller.__main__
import os

# Создание EXE файла
PyInstaller.__main__.run([
    'gui_manager.py',
    '--onefile',
    '--windowed',
    '--name=MEX_Trading_Bot_Manager',
    '--distpath=.',
    '--workpath=build',
    '--specpath=build'
])