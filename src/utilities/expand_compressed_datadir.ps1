# Script to zip NFSEG data files.
# Zipped files are needed to compress the data
# enough for transfer to and from the
# GitHub repository.
#
#
echo "======================================================================="
echo ""
echo "   This script unpacks zipped directories necessary at runtime."
echo ""
echo ""
echo "   Last Modified by: PMBremner - pbremner@sjrwmd.com"
echo "                     LMeridth  - lmeridth@sjrwmd.com"
echo "======================================================================="
echo ""

echo ""
echo "Unpacking the model directory . . ."
echo ""

# Expand the model data dir
Expand-Archive -LiteralPath model_update.zip -DestinationPath .\ -Force
#ls
#ls ..\

echo ""
echo "Unpacking the preprocess directory directory . . ."
echo ""

# Expand the model data dir
Expand-Archive -LiteralPath .\input_and_definition_files\preproc\wellpkg_update.zip -DestinationPath .\input_and_definition_files\preproc\ -Force


#echo "Process complete!"
echo ""
#pause

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
