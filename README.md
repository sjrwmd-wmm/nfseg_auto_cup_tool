# nfseg_auto_cup_tool
This repository hosts the District's Regulatory automated tool to calculate changes in
groundwater availability and other drawdown effects due to well additions or deletions
(cup - consumptive use permit) within the NFSEG groundwater model.

## Installation and Setup:
Download the zip file.
After the download is complete, unzip the tool to a directory on the local machine’s hard drive.
The tool unzips into its own directory, referred to as the *top-level directory*.
The last portion of the default Windows PATH when unzipping is usually not necessary.

Setup the tool for use by double-clicking the *setup.bat* script in the top-level directory.
A message may appear warning you about running the script.
Click the **Run-Anyway** option (sometimes this option only appears after clicking **More**).
The setup script does the following: 
- Search for the Python bundled with ArcGIS. 
- Automatically generate a file called *PY_PATH_autogen.txt* to store the PATH. Though the simulation tool does not require the auto-generated file (the tool auto searches for Python when the file is not present), having this file available will decrease the tool runtime significantly. If Python could not be found, then a **Failure** message will appear. If this occurs, or if the version is not the one desired by the User, it will be necessary to manually set Python in the tool to resolve the issue. Please contact the tool maintainers for help.
- Unzip the model data directory.

See the User's Guide in *docs* for complete documentation.
