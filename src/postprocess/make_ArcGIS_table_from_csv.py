# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to jwg (at) srwmd.org

import os
import time

def main():
    
    print "\nInitializing dh geoprocessing ..."
    print '    current datetime is {0}'.format(time.asctime(time.localtime()))

    import arcpy

    this_dir = os.getcwd()

    print "    Creating new dh file geodatabase ... "
    my_gdb = os.path.join(this_dir, 'dh.gdb')

    if arcpy.Exists(my_gdb):
        arcpy.Delete_management(my_gdb)

    arcpy.CreateFileGDB_management(this_dir, 'dh.gdb')
    arcpy.env.workspace = my_gdb

    cup_gdb = os.path.realpath('..\..\gis\cup.gdb')


    # Setup the new set of grid feature class
    grid_fc = "nfseg_v1_1_grid"

    if arcpy.Exists(grid_fc):
        print ("The grid_fc exists...deleting now to make new...")
        arcpy.Delete_management(grid_fc)


    print "    Copying model grid into new file geodatabase ...\n"
    # might be able to speed this up with Table View or Layer instead of fc copy ????
    arcpy.CopyFeatures_management(os.path.join(cup_gdb, grid_fc), grid_fc)

    arcpy.MakeFeatureLayer_management(grid_fc, "grid_layer")
    grid_layer = "grid_layer"

    for layer in range(1,4,2):
        print 'processing data for model-layer {0}'.format(layer)
        print '    current datetime is {0}'.format(time.asctime(time.localtime()))
        dh_label = 'dh_lyr{0}'.format(layer)
        # Set the local variables
        csvFileName = os.path.join(os.getcwd(), dh_label + '_tableFormat.csv')

        print("    import data into an ArcGIS table ...")
        if arcpy.Exists(dh_label):
            print("        Deleting prexisting table {0}".format(dh_label))
            arcpy.Delete_management(dh_label)

            print("    add csv file with dh data to file geodatabase ...")
        arcpy.TableToTable_conversion(csvFileName, my_gdb, dh_label)

        new_field_name = "dh_layer{0}".format(layer)

        print("    Add field for dh values")
        if arcpy.Exists(new_field_name):
            pass
        else:
            arcpy.AddField_management(grid_fc,new_field_name,"DOUBLE")

        print("    Join table to feature class ...")
        arcpy.AddJoin_management(grid_layer,"cell_address_2d",dh_label,"cellAddress2D")

        print("    Transfer data from table to feature class")
        #calc_expression = "!{0}.{0}_asc!".format(dh_label)
        calc_expression = "!{0}!".format(dh_label)
        arcpy.CalculateField_management(grid_layer,new_field_name,calc_expression, "PYTHON_9.3")
        
        print("    Removing join ...\n")
        arcpy.RemoveJoin_management(grid_layer,dh_label)

    print '\n    Finished ArcGIS processing of simulated dh field.'
    print '    current datetime is {0}'.format(time.asctime(time.localtime()))
    
    return
#
