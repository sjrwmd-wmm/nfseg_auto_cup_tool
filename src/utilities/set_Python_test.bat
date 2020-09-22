echo off
rem Set echo to only output as directed
rem
rem sim_cup.bat
rem Last Modified: 20191017. PMBremner, DDurden

echo =======================================================================
echo            NFSEG AUTOMATED WATER-USE PERMIT SIMULATION TOOL
echo:
echo    Main Batch script used to evaluate the impact of adding new wells
echo    to the NFSEG model.
echo:
echo    This Batch script is designed to read a user supplied csv file
echo    containing the id, location, and withdrawal rate of the wells
echo    requesting a permit.
echo:
echo    The new wells are processed utilizing MODFLOW, and the final
echo    results are output to two csv files and an updated mxd:
echo        1. .\^<your_input_filename^>_delta_q_summary.csv
echo        2. .\^<your_input_filename^>_global_budget_change.csv
echo        3. .\gis\dh.mxd
echo:
echo    Last Modified by: PMBremner - pbremner@sjrwmd.com
echo                      DDurden   - Douglas.Durden@srwmd.org
echo =======================================================================
echo:



rem ---------------------------------------
rem Set the PATH to the python executable for
rem enabling support on different computers
rem EXAMPLE: set PYCOM=C:\Python27\ArcGIS10.6\python
rem ---------------------------------------

setlocal EnableDelayedExpansion
SET PATHFILE=PY_PATH_autogen.txt


set PYCMD=C:\

if exist %PATHFILE% (
    
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
    
    echo !PYCMD!

) else (
    
    
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
    
    echo !PYCMD!

)

rem set PYCMD=C:\Python27\ArcGIS10.6\python

rem Display the PATH
echo:
echo:
echo arcpy Python version found: %PYCMD%
echo:
echo:

rem =======================================

PAUSE

EXIT
rem =======================================
