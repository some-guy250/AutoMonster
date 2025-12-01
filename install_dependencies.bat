@echo off
echo Installing AutoMonster dependencies...
echo.

echo Step 1: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 2: Installing av (video processing library) with pre-built binary...
pip install av==16.0.1 --only-binary=:all:

echo.
echo Step 3: Installing scrcpy-client (without dependencies to avoid av conflict)...
pip install --no-deps -r requirements-scrcpy.txt

echo.
echo Step 4: Installing remaining dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Note: You may see a warning about scrcpy-client requiring av^<10.0.0
echo This is expected and safe to ignore - av 16.0.1 is API-compatible.
echo.
echo You can now run the application!
