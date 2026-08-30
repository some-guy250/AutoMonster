@echo off
echo Installing AutoMonster dependencies...
echo.

python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo You can now run the application!
