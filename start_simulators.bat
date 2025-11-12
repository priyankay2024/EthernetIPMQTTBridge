@echo off
REM Start Multiple EthernetIP PLC Simulators
REM This script launches 3 simulator instances on different ports

echo ================================================================================
echo   Starting Multiple EthernetIP PLC Simulators
echo ================================================================================
echo.
echo   This will start 3 simulator instances:
echo     - PLC-1 on port 44818
echo     - PLC-2 on port 44819  
echo     - PLC-3 on port 44820
echo.
echo   Each simulator will open in a separate window.
echo   Close any window to stop that simulator.
echo.
echo ================================================================================
echo.

REM Start PLC-1 on port 44818
start "PLC-1 Simulator (Port 44818)" cmd /k "python real_plc_simulator.py --port 44818 --name PLC-1"
timeout /t 2 /nobreak >nul

REM Start PLC-2 on port 44819
start "PLC-2 Simulator (Port 44819)" cmd /k "python real_plc_simulator.py --port 44819 --name PLC-2"
timeout /t 2 /nobreak >nul

REM Start PLC-3 on port 44820
start "PLC-3 Simulator (Port 44820)" cmd /k "python real_plc_simulator.py --port 44820 --name PLC-3"

echo.
echo All simulators started!
echo.
echo Connect to them using:
echo   Device 1: Host=127.0.0.1, Port=44818
echo   Device 2: Host=127.0.0.1, Port=44819
echo   Device 3: Host=127.0.0.1, Port=44820
echo.
echo Press any key to exit this window (simulators will keep running)...
pause >nul
