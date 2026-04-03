@echo off
title DEDSEC TOOLBOX v10.0 GOLD - Build Script
color 0A
echo.
echo  ################################################################################
echo  ##                                                                            ##
echo  ##   DEDSEC TOOLBOX v10.0 GOLD - BUILD SCRIPT                                 ##
echo  ##   Compilando a Versao Final e Estavel                                      ##
echo  ##                                                                            ##
echo  ################################################################################
echo.

:: ── 1. Verificar Python ────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python nao encontrado! Instale em: https://www.python.org/downloads/
    echo     Marque "Add Python to PATH" durante a instalacao!
    pause & exit
)
echo [OK] Python encontrado.

:: ── 2. Instalar dependencias ─────────────────────
echo.
echo [*] Garantindo as dependencias mais recentes...
python -m pip install customtkinter Pillow pyinstaller speedtest-cli --quiet --upgrade
if errorlevel 1 (
    echo [!] Falha ao instalar dependencias.
    pause & exit
)
echo [OK] Dependencias prontas.

:: ── 3. Criar pastas necessarias ──────────────────────────────────────────
if not exist "assets" mkdir assets
if not exist "meus_scripts" mkdir meus_scripts
if not exist "OUTPUT" mkdir OUTPUT
echo [OK] Pastas verificadas.

:: ── 4. Gerar icone se nao existir ────────────────────────────────────────────────
if not exist "assets\icon.ico" (
    echo [*] Gerando icone DedSec...
    python -c "from PIL import Image, ImageDraw; import os; os.makedirs('assets', exist_ok=True); img = Image.new('RGBA', (256,256), (0,0,0,255)); d = ImageDraw.Draw(img); d.rectangle([6,6,250,250], outline=(0,255,65,255), width=3); d.ellipse([60,40,196,140], outline=(0,255,65,255), width=2); d.ellipse([85,65,115,95], fill=(0,255,65,255)); d.ellipse([141,65,171,95], fill=(0,255,65,255)); img.save('assets/icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)]); print('[OK] Icone gerado.')"
)

:: ── 5. Compilar com PyInstaller ───
echo.
echo [*] Compilando DEDSEC_TOOLBOX_v10.exe (aguarde)...
echo.

python -m PyInstaller --onefile --windowed --name "DEDSEC_TOOLBOX_v10" --icon "assets\icon.ico" --add-data "assets;assets" --hidden-import customtkinter --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageTk --hidden-import PIL.ImageEnhance --uac-admin --clean --distpath "OUTPUT" --workpath "temp_build" toolbox.py

if errorlevel 1 (
    echo.
    echo [!] ERRO FATAL NA COMPILACAO.
    pause & exit
)

:: ── 6. Limpeza de rastro ──────────────────────────────────────────
echo.
rmdir /s /q temp_build 2>nul
del DEDSEC_TOOLBOX_v10.spec 2>nul
if exist "dist" rmdir /s /q dist 2>nul
if exist "build" rmdir /s /q build 2>nul

echo.
echo  ################################################################################
echo  ##   [OK] DEDSEC TOOLBOX v10.0 GOLD ESTA PRONTO!                             ##
echo  ##   Arquivo gerado em: OUTPUT\DEDSEC_TOOLBOX_v10.exe                        ##
echo  ##   Nao esqueca de levar a pasta 'meus_scripts' junto se quiser plugins.     ##
echo  ################################################################################
echo.
pause
