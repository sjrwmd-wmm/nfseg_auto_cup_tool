echo off
rem Set echo to only output as directed
rem
rem sim_cup.bat
rem Last Modified: 20191017. PMBremner, DDurden



rem ---------------------------------------
rem Set the PATH to the python executable for
rem enabling support on different computers
rem EXAMPLE: set PYCOM=C:\Python27\ArcGIS10.6\python
rem ---------------------------------------


setlocal EnableDelayedExpansion
SET PATHFILE=PY_PATH_autogen.txt


set PYCMD=C:\

if exist %PATHFILE% (
    
    echo:
    echo Reading from file %PATHFILE%
    echo:
    
    for /f "delims=" %%n in ('find /c /v "" %PATHFILE%') do set "len=%%n"
    set "len=!len:*: =!"

    <%PATHFILE% (
    for /l %%l in (1 1 !len!) do (
        set "line="
        set /p "line="
        rem echo(!line!
    )
    )

    rem echo !line!

    rem Define the Python variable with what was found
    set PYCMD=!line!
    
    rem echo !PYCMD!

) else (
    
    echo:
    echo Did not find file %PATHFILE%
    echo Searching the system for arcpy. This may take a few moments . . .
    echo:
    
    rem Capture the current working directory
    SET CWD=%cd%


    rem Move to the root directory
    cd \

    rem Find arcpy and set it to an environment variable
    for /F "tokens=4" %%A in ('"dir python.exe /s /p | find "ArcGIS" | find "Python27" | find /N "Python27" | findstr /r \[[1]\]"') DO (SET PYCMD=%%A\python)


    rem Move back to the original working directory
    cd %CWD%
    
    rem echo !PYCMD!

)

rem set PYCMD=C:\Python27\ArcGIS10.6\python

rem Display the PATH
echo arcpy Python version found: %PYCMD%
echo:
echo:

rem =======================================


%PYCMD% src\sim_cup_main.py


PAUSE

EXIT
rem =======================================
