echo off

echo:
echo Setting up the NFSEG Reg Tool
echo:
echo This will take a few moments . . .
echo:
echo:
rem echo Finding ArcGIS Python . . .
echo:
CALL src\utilities\check_Python_version.bat
rem CALL src\utilities\read_PY_PATH_autogen.bat
echo:
echo:
rem echo Unpacking directories . . .
echo:
Powershell.exe -NoProfile -ExecutionPolicy Bypass -File src\utilities\uncompress_datadir.ps1
echo:
echo:
echo Process complete
echo:

PAUSE

EXIT
