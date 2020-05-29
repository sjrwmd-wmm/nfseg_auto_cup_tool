# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to jwg (at) srwmd.org

print "\nInitializing process for intersecting withdrawal locations with model grid (takes a few seconds) ...\n"

import os
import arcpy

this_dir = os.getcwd()
my_gdb = os.path.join(os.getcwd(), 'wellpkg_update.gdb')
arcpy.env.workspace = my_gdb
cup_gdb = os.path.realpath('..\..\gis\cup.gdb')

# Set the local variables
in_Table =os.path.join(os.getcwd(), "withdrawal_point_locations_and_rates.csv")
#in_Table = "test_input.csv"
x_coords = "XCoord"
y_coords = "YCoord"
cup_wells_layer_state_plane_north = "cup_wells_layer_state_plane_north"
cup_wells_layer = "cup_wells_layer"

cupWells_fc = r"cup_wells_fc"
cupWells_fc_exported_to_gis_dir = r"cup_wells"

# Set the spatial reference
spRef_state_plane_north = os.path.join(this_dir, "state_plane_north.prj")
spRef_nfseg = os.path.join(this_dir, "nfseg_v1_1_grid.prj")

print "Importing x,y coordinates for withdrawal points ..."
# Make the XY event layer...
if arcpy.Exists(cup_wells_layer_state_plane_north):
    arcpy.Delete_management(cup_wells_layer_state_plane_north)

#arcpy.MakeXYEventLayer_management(in_Table, x_coords, y_coords, cup_wells_layer, spRef_nfseg)
arcpy.MakeXYEventLayer_management(in_Table, x_coords, y_coords, cup_wells_layer_state_plane_north, spRef_state_plane_north)

# Print the total rows
number_of_withdrawl_points = arcpy.GetCount_management(cup_wells_layer_state_plane_north)
print "    Imported data for {0} withdrawal points\n".format(number_of_withdrawl_points)

# project new cup wells layer
if arcpy.Exists(cup_wells_layer):
    arcpy.Delete_management(cup_wells_layer)

arcpy.Project_management(cup_wells_layer_state_plane_north, cup_wells_layer, spRef_nfseg)

if arcpy.Exists(cupWells_fc):
    arcpy.Delete_management(cupWells_fc)

print "    Projected locations of {0} withdrawal points\n".format(number_of_withdrawl_points)

# export to feature class
#arcpy.CopyFeatures_management(cup_wells_layer, cupWells_fc)
arcpy.CopyFeatures_management(cup_wells_layer, cupWells_fc)

print "    Copied layer containing withdrawal points to new feature class\n"

# Set local parameters
inFeatures = cupWells_fc
idFeatures = os.path.join(cup_gdb, "nfseg_v1_1_grid")
outFeatures = os.path.join(my_gdb, "cup_wells_with_grid_info")
outFeatures_for_export_to_cup_gdb = os.path.join(cup_gdb, "cup_wells_with_grid_info")
csvOutputFile = os.path.join(this_dir, "wells_to_add.csv")

print "Intersecting withdrawal point locations with model grid ...\n"

# Process: Use the Identity function
if arcpy.Exists(outFeatures):
    arcpy.Delete_management(outFeatures)

arcpy.Identity_analysis (inFeatures, idFeatures, outFeatures)

if arcpy.Exists(outFeatures_for_export_to_cup_gdb):
    arcpy.Delete_management(outFeatures_for_export_to_cup_gdb)

print("Identity operation complete, now copy features to cup.gdb and export .csv file")
arcpy.CopyFeatures_management(outFeatures, os.path.join(cup_gdb, outFeatures_for_export_to_cup_gdb))


if arcpy.Exists(csvOutputFile):
    arcpy.Delete_management(csvOutputFile)

arcpy.ExportXYv_stats(outFeatures, ["WellId","layer", "row", "col", "Q_cfd"], "COMMA", csvOutputFile, "ADD_FIELD_NAMES")

print "\nFinished (row, col) identification for withdrawal points!\n\n"
