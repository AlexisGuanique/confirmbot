@echo off
echo ========================================
echo ConfirmaBot - Script de Construccion DEBUG
echo ========================================
echo.

echo [1/4] Limpiando archivos anteriores...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

echo [2/4] Generando archivo .spec (con consola para debug)...
pyinstaller --onefile --icon="favicon.ico" --name=ConfirmaBotHostinger-Debug main.py

echo [3/4] Verificando que el ejecutable se creo...
if exist "dist\ConfirmaBotHostinger-Debug.exe" (
    echo ✅ Ejecutable DEBUG creado exitosamente!
    echo 📁 Ubicacion: dist\ConfirmaBotHostinger-Debug.exe
) else (
    echo ❌ Error: No se pudo crear el ejecutable DEBUG
    pause
    exit /b 1
)

echo [4/4] Creando carpetas necesarias...
if not exist "dist\images" mkdir "dist\images"
if not exist "dist\linkedin_accounts" mkdir "dist\linkedin_accounts"

echo.
echo ========================================
echo    ✅ Construccion DEBUG Completada
echo ========================================
echo.
echo 📁 Ejecutable DEBUG: dist\ConfirmaBotHostinger-Debug.exe
echo 📁 Carpeta de imagenes: dist\images\
echo 📁 Carpeta de cuentas: dist\linkedin_accounts\
echo.
echo NOTA: Esta version incluye consola para debug.
echo Las carpetas 'images' y 'linkedin_accounts' apareceran
echo automaticamente al lado del ejecutable cuando se ejecute.
echo.
pause
