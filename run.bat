@echo off
title FlowMorph Studio - Launcher
cd /d "%~dp0"

echo ============================================================
echo           FlowMorph Studio - Video Interpolator
echo    Dense Optical Flow Frame Rate Upsampling Platform
echo ============================================================
echo.
echo [1/2] Verifying Python environment and dependencies...

python -c "import customtkinter, cv2, numpy, PIL, imageio_ffmpeg" 2>nul
if %errorlevel% neq 0 (
    echo [NOTICE] Required packages missing. Installing dependencies...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install required packages.
        echo Please ensure Python is added to your system PATH and internet is available.
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed successfully.
    echo.
)

echo [2/2] Launching FlowMorph Studio Desktop UI...
echo.
start "" pythonw main.py
if %errorlevel% neq 0 (
    python main.py
)
exit /b 0