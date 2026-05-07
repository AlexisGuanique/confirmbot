@echo off
REM Ejecutor: clic en extensión user agent (coordenadas del creator).
REM Uso: run_user_agent_extension.bat
REM      run_user_agent_extension.bat --browser-id 2
REM      run_user_agent_extension.bat --full
cd /d "%~dp0"
python -m app.creator.user_agent_actions %*
exit /b %ERRORLEVEL%
