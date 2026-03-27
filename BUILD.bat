@echo off
title REDSEC TOOLBOX v8.0 - Build Script
color 0A
echo.
echo  ################################################################################
echo  ##                                                                            ##
echo  ##   REDSEC TOOLBOX v8.0 - BUILD SCRIPT                                       ##
echo  ##   Compilando Python para .exe com PyInstaller                             ##
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

:: ── 2. Instalar dependencias via python -m pip ─────────────────────
echo.
echo [*] Instalando dependencias...
python -m pip install customtkinter Pillow pyinstaller speedtest-cli --quiet --upgrade
if errorlevel 1 (
    echo [!] Falha ao instalar dependencias. Verifique sua conexao.
    pause & exit
)
echo [OK] Dependencias instaladas.

:: ── 3. Criar pasta assets ──────────────────────────────────────────
if not exist "assets" mkdir assets
echo [OK] Pasta assets pronta.

:: ── 4. Verificar imagens ──────────────────────────────────────────
echo.
echo [*] Verificando imagens em assets\...
if not exist "assets\robot.jpg"           echo [!] AVISO: assets\robot.jpg nao encontrado
if not exist "assets\hands_ascii.jpg"     echo [!] AVISO: assets\hands_ascii.jpg nao encontrado
if not exist "assets\dark_triad.jpg"      echo [!] AVISO: assets\dark_triad.jpg nao encontrado
if not exist "assets\pixel_pc.jpg"        echo [!] AVISO: assets\pixel_pc.jpg nao encontrado
if not exist "assets\samurai.jpg"         echo [!] AVISO: assets\samurai.jpg nao encontrado
if not exist "assets\dedsec_skull.gif"    echo [!] AVISO: assets\dedsec_skull.gif nao encontrado (splash principal)
if not exist "assets\we_are_coming.gif"   echo [!] AVISO: assets\we_are_coming.gif nao encontrado (tela WE ARE COMING)
if not exist "assets\eye_screensaver.gif" echo [!] AVISO: assets\eye_screensaver.gif nao encontrado (screensaver)
if not exist "assets\b6e1b7f9ef3227a4294385d9980a50d3.gif" echo [!] AVISO: assets\b6e1b7f9ef3227a4294385d9980a50d3.gif nao encontrado (gif sidebar)
echo [OK] Verificacao concluida.

:: ── 5. Gerar icone ────────────────────────────────────────────────
if not exist "assets\icon.ico" (
    echo [*] Gerando icone DedSec...
    python -c "from PIL import Image, ImageDraw; import os; os.makedirs('assets', exist_ok=True); img = Image.new('RGBA', (256,256), (0,0,0,255)); d = ImageDraw.Draw(img); d.rectangle([6,6,250,250], outline=(0,255,65,255), width=3); d.ellipse([60,40,196,140], outline=(0,255,65,255), width=2); d.ellipse([85,65,115,95], fill=(0,255,65,255)); d.ellipse([141,65,171,95], fill=(0,255,65,255)); img.save('assets/icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)]); print('[OK] Icone gerado.')"
)

:: ── 6. Compilar com python -m PyInstaller (corrige erro de PATH) ───
echo.
echo [*] Compilando para .exe (aguarde 1-3 minutos)...
echo.

python -m PyInstaller --onefile --windowed --name "REDSEC_TOOLBOX_v8" --icon "assets\icon.ico" --add-data "assets;assets" --hidden-import customtkinter --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageTk --hidden-import PIL.ImageEnhance --uac-admin --clean toolbox.py

if errorlevel 1 (
    echo.
    echo [!] Falha na compilacao! Verifique os erros acima.
    pause & exit
)

:: ── 7. Mover para OUTPUT ──────────────────────────────────────────
echo.
if not exist "OUTPUT" mkdir OUTPUT
copy "dist\REDSEC_TOOLBOX_v8.exe" "OUTPUT\" >nul
rmdir /s /q build 2>nul
del REDSEC_TOOLBOX_v8.spec 2>nul

echo.
echo  ################################################################################
echo  ##   [OK] COMPILACAO CONCLUIDA!                                              ##
echo  ##   Arquivo: OUTPUT\REDSEC_TOOLBOX_v8.exe                                    ##
echo  ################################################################################
echo.
pause
