# Release Notes
This document contains a running summary of changes with each release version. Ordered from the most recent version to the oldest.

## Version 3.0 -- 26 Feb 2021

This repository was migrated from the SJR District GitHub server to this current (cloud) server 24 Feb 2021. The full **commit** and **issues** histories were preserved, though the first release *v2.0* was unable to be migrated. The first release is archived on a SJR District network drive system.

### Highlights of changes since version 2.0
- 43 commits, over 20,000 line changes, 18 issues closed by 2 contributors
- Numerous updates to the documentation
- Numerous lines of code were cleaned up and many descriptive code comments were cleaned up or added
- New functionality implemented, many changes made to old functionality

### Specific updates and fixes
1. Sent more of the existing print statements and error statements to the log file
2. Standardized internal directory operations that capture the current working directory and its parent during runtime. The change replaced the dependence on forward or backward slashes by allowing os.path to determine the OS's path separator, and should be a more platform independent method.
3. Made changes to how the Tool replaces an existing results folder with the same name as the current run
4. File cleanup
    1. Some files generated during runtime existed amongst the input files within the reference directories in the repository. These files were copied to the results folder along with actual input files. Those generated files were removed from the repository.
    2. Relocated old model heads processing input files used in previous versions of the Reg Tool. The files are no longer used by the Tool, but were used for NFSEG v1.1 calibration in some capacity. They are now located in an archived folder outside of the repository.
    3. Replaced the zipped dQ input directory with the uncompressed version.
    4. Relocated old dQ related files to an archived folder outside of the repository.
    5. Replaced the *gis/projections.zip* file with the *gis/projections* directory. Only the projection files needed for the current run (only 2 of 3 files) are copied over from the reference *gis/projections* directory to the results directory.
    6. Relocated archived documentation.
5. Updated the gage input files to the current versions
6. Overhaul of the preprocess directory
    1. The zipped preprocess directory is now expanded only once during the Tool setup on a User's computer, rather than unzipped into the results folder during runtime. Now, the relevant files are referenced, but not copied to a results folder.
    2. Revamped the cup well gdb processing:
        * Cleaned up the process for locating cup well coordinates within the NFSEG grid.
        * Removed *wellpkg_update.gdb*. Previously, the cup well locations were saved to *wellpkg_update.gdb*, and then those contents were copied to the *cup.gdb*. Now, the cup well locations are saved directly to the *cup.gdb* without using the *wellpkg_update.gdb* as an intermediate step.
        * Modified the inputs to the script that processes and locates the cup wells on the grid to now directly accept the grid and map projection filenames and PATHs in order to reduce duplication (filenames and PATHs for map projections were defined in both this processing script and MAIN).
        * Renamed the cup well processing/locating script to show evolutionary history.
7. The budget directory no longer contributes any input files to the current run. An empty budget directory is now created in the results folder and filled with files generated during runtime.
8. Complete overhaul of the scripts and methods used to read model heads and process and map changes in heads.
    1. Fully replaced the PEST-based method to extract model-wide heads for layers 1 and 3 with a dedicated Fortran executable and a supporting Python script to extract model heads for all layers, and to map layers 1, 3, and 5. In the same process, the area-weighted lake heads are calculated for all model layers. The Fortran routine was based off the original routine supplied by Wei Jin and generalized to be used for other models. The new routine extracts heads and for all model layers, processes the change in heads (dh) as stress period 2 minus 1, and calculates the area-averaged lake heads and dh. The extracted heads and dh are output to file for all layers.
    2. The head extraction routines and lake files have been separated and reorganized into the *src* and *input_files_and_definitions* directories.
    3. Added the files that link the LakeIDs and LakeNames for each of the included list sources: Trey, Vito, and JohnGood. They are now copied to the results folder.
    4. Replaced the dh.zip file in the *input_and_definition_files/postproc* directory with the uncompressed dh directory. Now, only the relevant files from the dh directory are copied to the results folder. The reference dh directory in input_and_definitions_files now includes the input_control_file for the new head extraction routines, as well as retaining (for now) the PEST related input files for the old method of processing heads.
    5. Replaced the zipped dh.mxd template file with the unzipped version in the GIS directory and copied to the results directory during runtime.
    6. Rewrote the *make_ArcGIS_table_from_csv* script, which now accepts the model heads change file as output from the new Fortran routine (no reformatting needed). Many simplifications were made, including:
        * The *cup.gdb* grid table has been reduced substantially (~200MB to ~70MB)
        * The *dh.gdb* is no longer created during runtime
        * The make_ArcGIS script uses preexisting (and natural) reference data to join multiple columns of data at once, rather than multiple files and joins to add data columns
        * Now supports easy addition of model layers
        * MXD now updated to show layer 5 alongside 1,3 (previously only showed layers 1,3) and no longer links to deprecated dh.gdb. All 3 layers were scaled
9. Partial overhaul of the springflow and gaged reach change in flux (dQ) post-processing and generation of the dQ report file
    1. Added new info file that connects stationID to station names has been added to fix the issue of only SR waterbodies showing in the report.
    2. Made substantial simplifications and additions to the script that generates the change in gage fluxes summary report, including:
        * Added SJR waterbodies to the output, as well as including a new file listing all gage stations,
        * Added Water Management District ownership column for each waterbody,
        * Overhauled, simplified, and cleaned up virtually all functions in the script, as well as adding many comments describing processes,
        * Replaced a default (made-up) value with zero for extremely small (>1e-10) streamflow changes.

## Version 2.0 -- 26 Oct 2020
Major upgrade from version 1.1

### Highlights of changes since version 1.1
- 83 commits, over 30,000 line changes, 3 contributors
- New documentation
- Numerous lines of code were cleaned up and many descriptive code comments were cleaned up or added
- Some new functionality implemented, many changes made to old functionality
- Implemented a new main script for the workflow
- First release on GitHub

### Specific updates and fixes
Please see the commits history for a full list of changes

## Version 1.1 -- Oct 2019
Original version 1.0 was no longer working. Updated portions of the code to bring back up to a working state. Some input files were updated. No major changes in workflow from version 1.0.

## Version 1.0 -- 2016(?)
Original version by Trey Grubbs
