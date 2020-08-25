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
import arcpy
# TODO: Fix inputs
def main(currentworkingdir, gis_dir, grid_featureclass, logfile):
    
    currentmessage = ('\tInitializing dh geoprocessing ...\n' +
    '\tcurrent datetime is {0}'.format(time.asctime(time.localtime())))
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    # TODO: Handle directories
    #currentworkingdir = os.getcwd()
    
    
    currentmessage = ('\tCreating new dh file geodatabase ...\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    my_gdb = os.path.join(currentworkingdir, 'dh.gdb')
    
    if arcpy.Exists(my_gdb):
        arcpy.Delete_management(my_gdb)
    
    arcpy.CreateFileGDB_management(currentworkingdir, 'dh.gdb')
    arcpy.env.workspace = my_gdb
    
    #cup_gdb = os.path.realpath('..\..\gis\cup.gdb')
    cup_gdb = os.path.join(gis_dir,'cup.gdb')
    
    
    # Setup the new set of grid feature class
    #grid_featureclass = "nfseg_v1_1_grid"
    
    if arcpy.Exists(grid_featureclass):
        currentmessage = ("\tThe grid_featureclass exists...deleting now to make new...\n")
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write(currentmessage)
        arcpy.Delete_management(grid_featureclass)
    
    
    currentmessage = ('\tCopying model grid into new file geodatabase ...\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    # might be able to speed this up with Table View or Layer instead of fc copy ????
    arcpy.CopyFeatures_management(os.path.join(cup_gdb, grid_featureclass), grid_featureclass)

    arcpy.MakeFeatureLayer_management(grid_featureclass, "grid_layer")
    grid_layer = "grid_layer"

    for layer in range(1,4,2):
        currentmessage = ('\tprocessing data for model-layer {0}\n' +
                          '\t\tcurrent datetime is {1}\n'.format(layer,time.asctime(time.localtime())))
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write(currentmessage)
        dh_label = 'dh_lyr{0}'.format(layer)
        # Set the local variables
        csvFileName = os.path.join(os.getcwd(), dh_label + '_tableFormat.csv')
        
        
        currentmessage = ('\timport data into an ArcGIS table ...\n')
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write(currentmessage)
        #
        if arcpy.Exists(dh_label):
            currentmessage = ('\tDeleting prexisting table {0}\n'.format(dh_label))
            print (currentmessage)
            with open(logfile,'a') as lf: lf.write(currentmessage)
            arcpy.Delete_management(dh_label)
            
            currentmessage = ('\tadd csv file with dh data to file geodatabase ...\n')
            print (currentmessage)
            with open(logfile,'a') as lf: lf.write(currentmessage)
        #
        arcpy.TableToTable_conversion(csvFileName, my_gdb, dh_label)
        
        new_field_name = "dh_layer{0}".format(layer)
        
        currentmessage = ('\tAdd field for dh values\n')
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write(currentmessage)
        #
        if arcpy.Exists(new_field_name):
            pass
        else:
            arcpy.AddField_management(grid_featureclass,new_field_name,"DOUBLE")

        currentmessage = ('\tJoin table to feature class ...\n')
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write(currentmessage)
        #
        arcpy.AddJoin_management(grid_layer,"cell_address_2d",dh_label,"cellAddress2D")
        
        currentmessage = ('\tTransfer data from table to feature class\n')
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write(currentmessage)
        #
        #calc_expression = "!{0}.{0}_asc!".format(dh_label)
        calc_expression = "!{0}!".format(dh_label)
        arcpy.CalculateField_management(grid_layer,new_field_name,calc_expression, "PYTHON_9.3")
        
        print("    Removing join ...\n")
        arcpy.RemoveJoin_management(grid_layer,dh_label)
    #
    
    currentmessage = ('\tFinished ArcGIS processing of simulated dh field.\n' +
                      '\t\tcurrent datetime is {0}'.format(time.asctime(time.localtime())))
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    return
#
