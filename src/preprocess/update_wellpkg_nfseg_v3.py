# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to pbremner (at) sjrwmd.com

# Modified: 20190917. DDurden
# The present program version calls the ArcGIS "intersect" command rather
# than the ArcGis "identity" command to enable its use with a "Basic" 
# ArcGis license.  This change is at line 85.

# Modified: 20190927. PMBremner
# Relocate some of the print statements to correspond to the actions described
# in the commands that follow them.

# Modified: 20210121. PMBremner
# Removed creation of separate geodatabase "wellpkg_update.gdb"
# The added wells are now put directly into the cup.gdb
# instead of creating wellpkg_update.gdb and then copying
# its contents to cup.gdb.
# Various cleanup associated with the above change.
# Swapped Trey's email for pbremner to report errors.
#==============================================================================



import os
import arcpy


def main(SpatialReference, workingdir, gis_dir, grid_featureclass, grid_featureclass_proj, logfile):
    
    currentmessage = ("\n\tInitializing process for intersecting withdrawal locations with model grid (takes a few seconds) . . .\n")
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    # Define the cup geodatabase and grid feature class
    cup_gdb = os.path.join(gis_dir,'cup.gdb')
    arcpy.env.workspace = cup_gdb
    
    
    # ---------------------------------------------
    # Setup the new Event Layer
    # ---------------------------------------------
    
    # Set the local variables
    in_Table =os.path.join(workingdir, 'withdrawal_point_locations_and_rates.csv')
    x_coords = "XCoord"
    y_coords = "YCoord"
    cup_wells_layer_state_plane_north = 'cup_wells_layer_state_plane_north'
    cup_wells_layer = 'cup_wells_layer'
    cupWells_fc = r'cup_wells_fc' # feature class
    
    
    
    # Make the XY event layer...
    currentmessage = ("\tCleaning out old cup well event layer")
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    if arcpy.Exists(cup_wells_layer_state_plane_north):
        arcpy.Delete_management(cup_wells_layer_state_plane_north)


    # Make the XY event layer...
    currentmessage = ("\tImporting x,y coordinates for withdrawal points")
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    # syntax: MakeXYEventLayer_management (table, in_x_field, in_y_field, out_layer, {spatial_reference}, {in_z_field})
    #arcpy.MakeXYEventLayer_management(in_Table, x_coords, y_coords, cup_wells_layer, grid_featureclass_proj)
    arcpy.MakeXYEventLayer_management(in_Table, x_coords, y_coords, cup_wells_layer_state_plane_north, SpatialReference)
    
    # ---------------------------------------------
    
    
    # Count the total number of added wells
    number_of_withdrawl_points = arcpy.GetCount_management(cup_wells_layer_state_plane_north)
    currentmessage = ("\t{0} withdrawal points imported\n".format(number_of_withdrawl_points))
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    # ---------------------------------------------
    # Get the Event Layer saved into a FeatureClass
    # ---------------------------------------------
    
    # Remove any existing cup wells layer
    if arcpy.Exists(cup_wells_layer):
        arcpy.Delete_management(cup_wells_layer)
    
    # Apply well info to new projection layer (NFSEG is Albers)
    # arcpy.Project_management(Input, Output, Projection)
    arcpy.Project_management(cup_wells_layer_state_plane_north, cup_wells_layer, grid_featureclass_proj)
    
    currentmessage = ('\tWithdrawal points projected\n\tSaving to feature class\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    # Save to a feature class
    if arcpy.Exists(cupWells_fc):
        arcpy.Delete_management(cupWells_fc)
    arcpy.CopyFeatures_management(cup_wells_layer, cupWells_fc)
    
    currentmessage = ("\tSaved feature class\n")
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    # ---------------------------------------------
    
    # ---------------------------------------------
    # Find the Model Grid Cells that Intersect
    # with the coordinates of the well(s)
    # and save to gdb
    #
    # 1. Find the Model Grid Rows, Columns that
    #    intersect the cup well X,Y coord
    #
    # 2. Output data to .csv file
    #
    # Process: Use the Identity function
    #    -  Replaced arcpy.Identity_analysis with
    #       arpy.Intersect_analysis
    #       because Identity was not available
    #       with a basic ArcMap license
    #       (20190917)
    # ---------------------------------------------
    
    # Set local parameters
    outFeatures = os.path.join(cup_gdb, "cup_wells_with_grid_info")
    csvOutputFile = os.path.join(workingdir, "wells_to_add.csv")
    
    currentmessage = ("\tIntersecting withdrawal point locations with model grid ...\n")
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    # Find Model Row,Column points
    if arcpy.Exists(outFeatures):
        arcpy.Delete_management(outFeatures)
    
    # Find the intersting points
    # syntax: Intersect_analysis (in_features, out_feature_class, {join_attributes}, {cluster_tolerance}, {output_type})
    #arcpy.Identity_analysis (cupWells_fc, grid_featureclass, outFeatures)
    arcpy.Intersect_analysis([cupWells_fc, grid_featureclass], outFeatures)
    
    
    currentmessage = ('\tIntersection complete\n\tExporting well(s) row,column,layer information to .csv file ...\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    # Export to a .csv file
    if arcpy.Exists(csvOutputFile):
        arcpy.Delete_management(csvOutputFile)

    arcpy.ExportXYv_stats(outFeatures, ["WellId","layer", "row", "col", "Q_cfd"],
                          "COMMA", csvOutputFile, "ADD_FIELD_NAMES")
    
    currentmessage = ("\n\tFinished (row, col) identification for withdrawal points\n\n")
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    return
#  END DEF
