# Script to zip NFSEG data files.
# Zipped files are needed to compress the data
# enough for transfer to and from the
# GitHub repository.
#
#

echo "This script controls compression and expansion of data files and directories."
echo "--   Compression prepares the data files for transfer to the GitHub repository"
echo "--   Expansion is used to initialize the data files for use after retrieving from GitHub"
echo ""
echo "Please choose between compressing or expanding the data"
echo ""

$CompressFlag = Read-Host "Compress or Expand data?"

# Initialize a flag dictating whether to delete the unneeded files
$dflag_selection = Read-Host "Select whether to delete unneeded files when complete: Y or N"
if ($dflag_selection -eq "N") {
    [bool] $DeleteFlag = $false
    }
elseif ($dflag_selection -eq "Y") {
    echo ""
    $dflag_confirm = Read-Host "Are you sure you want to delete files when complete? Y or N"
    if ($dflag_confirm -eq "Y") {
        [bool] $DeleteFlag = $true
        }
    else {
     [bool] $DeleteFlag = $false
     }
    }
else {
    # If the selection doesn't match Y or N, then default to false
    [bool] $DeleteFlag = $false
    }

echo ""
echo "Selection input:  $CompressFlag"
echo ""

if ($CompressFlag -eq "Compress") {
    echo "Compressing Data..."
    echo ""
    
    # Compress the input_and_definition_files\preproc dirs
    Compress-Archive -Path ..\input_and_definition_files\preproc\wellpkg_update -DestinationPath ..\input_and_definition_files\preproc\wellpkg_update.zip -Force
    
    # Compress the input_and_definition_files\postproc dir
    Compress-Archive -Path ..\input_and_definition_files\postproc -DestinationPath ..\input_and_definition_files\postproc.zip -Force
    
    # Compress the model data dir
    Compress-Archive -Path ..\model_update -DestinationPath ..\model_update.zip -Force
    
    # Compress the GIS data dir
    Compress-Archive -Path ..\gis\cup.gdb -DestinationPath ..\gis\cup.gdb.zip -Force
    Compress-Archive -Path ..\gis\dh.gdb -DestinationPath ..\gis\dh.gdb.zip -Force
        
    if ($DeleteFlag -eq $true) {
        echo "Deleting the original directories..."
        echo ""
        Remove-Item '..\input_and_definition_files\preproc\wellpkg_update' -Recurse
        Remove-Item '..\input_and_definition_files\postproc' -Recurse
        Remove-Item '..\model_update' -Recurse
        Remove-Item '..\gis\cup.gdb' -Recurse
        Remove-Item '..\gis\dh.gdb' -Recurse
        }
    
    }
elseif ($CompressFlag -eq "Expand") {
    echo "Expanding Data..."
    echo ""
    
    # Expand the input_and_definition_files\preproc dirs
    Expand-Archive -LiteralPath ..\input_and_definition_files\preproc\wellpkg_update.zip -DestinationPath ..\input_and_definition_files\preproc -Force
    
    # Expand the input_and_definition_files\postproc dir
    Expand-Archive -LiteralPath ..\input_and_definition_files\postproc.zip -DestinationPath ..\input_and_definition_files -Force
    
    # Expand the model data dir
    Expand-Archive -LiteralPath ..\model_update.zip -DestinationPath ..\ -Force
    
    # Expand the model data dir
    Expand-Archive -LiteralPath ..\gis\cup.gdb.zip -DestinationPath ..\gis -Force
    Expand-Archive -LiteralPath ..\gis\dh.gdb.zip -DestinationPath ..\gis -Force
    
    if ($DeleteFlag -eq $true) {
        echo "Deleting the zip files..."
        echo ""
        Remove-Item '..\input_and_definition_files\preproc\wellpkg_update.zip'
        Remove-Item '..\input_and_definition_files\postproc.zip'
        Remove-Item '..\model_update.zip'
        Remove-Item '..\gis\cup.gdb.zip'
        Remove-Item '..\gis\dh.gdb.zip'
        }
    }
else {
    echo "Selection not recognized..."
    echo ""
    }


echo "Process complete!"
echo ""
pause

#case_007c_eval.mxd
#nfseg_auto_preproc_test.mxd
#nfseg_v1_1_grid.cpg
#nfseg_v1_1_grid.dbf
#nfseg_v1_1_grid.sbn
#nfseg_v1_1_grid.sbx
#nfseg_v1_1_grid.shp
#nfseg_v1_1_grid.shp.xml
#nfseg_v1_1_grid.shx
#temp.mxd
# Compress the grid geodatabase
#Compress-Archive -LiteralPath ..\input_and_definition_files\preproc\wellpkg_update\nfseg_v1_1_grid.dbf -DestinationPath ..\input_and_definition_files\preproc\wellpkg_update\nfseg_v1_1_grid.dbf.zip -Force

#Compress-Archive -Path ..\input_and_definition_files\preproc\wellpkg_update -DestinationPath ..\input_and_definition_files\preproc\wellpkg_update -Force
