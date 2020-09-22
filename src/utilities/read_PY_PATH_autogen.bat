echo off
rem Set echo to only output as directed
rem
rem 
rem Last Modified: 20191025. PMBremner, DDurden

echo =======================================================================
echo:
echo    This script reads the PATH to arcpy, the Python version
echo    that is bundled with ArcMap, from the file:
echo:
echo    PY_PATH_autogen.txt
echo:
echo:
echo    The purpose of this script was originally to test reading
echo    the PATH from file, but is also useful just to see which
echo    Python version is being used by the simulation tool.
echo:
echo:
echo    Last Modified by: PMBremner - pbremner@sjrwmd.com
echo                      DDurden   - Douglas.Durden@srwmd.org
echo =======================================================================
echo:


echo:
echo    Reading the ArcMap Python (arcpy) from PY_PATH_autogen.txt . . .
echo    The acrpy PATH is:
echo:
echo:


SET PATHFILE=PY_PATH_autogen.txt

setlocal EnableDelayedExpansion

for /f "delims=" %%n in ('find /c /v "" %PATHFILE%') do set "len=%%n"
set "len=!len:*: =!"

<%PATHFILE% (
  for /l %%l in (1 1 !len!) do (
    set "line="
    set /p "line="
    rem echo(!line!
  )
)


rem Display the PATH
echo %line%


echo:
echo:

rem PAUSE

rem EXIT
rem =======================================
