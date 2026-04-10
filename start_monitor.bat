@echo off
echo [1/3] Checking environment...
if not exist .env (
    echo [ERROR] .env file missing! Please create it first.
    pause
    exit
)

echo [2/3] Installing/Updating dependencies...
call npm install --registry=https://registry.npmmirror.com

echo [3/3] Launching Development Server...
echo.
echo Dashboard will be available at http://localhost:5173
echo.
call npm run dev

pause