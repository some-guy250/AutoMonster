@echo off
echo Installing AutoMonster dependencies...
echo.

echo Step 1: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 2: Installing setuptools (provides pkg_resources)...
python -m pip install --upgrade setuptools

echo.
echo Step 3: Installing av (video processing library) with pre-built binary...
python -m pip install av==16.0.1 --only-binary=:all:

echo.
echo Step 4: Installing scrcpy-client (without dependencies to avoid av conflict)...
python -m pip install --no-deps -r requirements-scrcpy.txt

echo.
echo Step 5: Installing remaining dependencies...
python -m pip install -r requirements.txt

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo You can now run the application!
pause