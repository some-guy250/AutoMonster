:: filepath: /c:/Users/Rodolfo/Desktop/C/Desktop/Code/python/AutoMonster/replace.bat
@echo off
setlocal enabledelayedexpansion

:: Get parameters
set "source=%~1"
set "destination=%~2"

:: Check if parameters are provided
if "%source%"=="" (
    echo Source file not specified
    exit /b 1
)
if "%destination%"=="" (
    echo Destination path not specified
    exit /b 1
)

:: Check if source exists
if not exist "%source%" (
    echo Source file does not exist: %source%
    exit /b 1
)

:: Try to delete destination if it exists
if exist "%destination%" (
    del /F "%destination%" >nul 2>&1
    if errorlevel 1 (
        echo Failed to delete existing file: %destination%
        exit /b 1
    )
)

:: Move the new file
move /Y "%source%" "%destination%" >nul 2>&1
if errorlevel 1 (
    echo Failed to move file from %source% to %destination%
    exit /b 1
)

echo File replaced successfully
exit /b 0