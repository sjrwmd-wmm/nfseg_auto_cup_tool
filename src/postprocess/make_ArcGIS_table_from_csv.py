# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to pbremner (at) sjrwmd.com

import os
import arcpy
# Import internal python scripts
from utilities import basic_utilities as bscut


def main(dh_layer_dictionary, currentworkingdir, gis_dir, grid_featureclass, logfile):
    
    # Structure of the input dh layer properties:
    # dh_layer_dictionary = {'datafile':'','joinField':dc(refcolumn),'fieldList':[]}
    
    
    # Print out the date and time of processing
    currentmessage = ('\tInitializing dh geoprocessing ...\n'
                      + bscut.datetime() + '\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    # Set the working environment to the cup.gdb
    currentmessage = ('\n\tlinking to the cup geodatabase ...\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    #
    my_gdb = os.path.join(gis_dir, 'cup.gdb')
    arcpy.env.workspace = my_gdb
    
    # Setup the new set of grid feature class
    #grid_featureclass = "nfseg_v1_1_grid"
    
    # From ArcGIS Doc:
    # Creates a feature layer from an input feature class or layer file.
    # The layer that is created by the tool is temporary and will not
    # persist after the session ends unless the layer is saved to disk or
    # the map document is saved.
    arcpy.MakeFeatureLayer_management(grid_featureclass, "grid_layer")
    #grid_layer = "grid_layer"
    
    
    # Convert the data into a TableView
    currentmessage = ('\timporting data into an ArcGIS table ...\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    #
    inTable = os.path.join(currentworkingdir, dh_layer_dictionary['datafile']) # The dh data
    outLocation = my_gdb
    outTable = 'dh_lyrs'
    arcpy.TableToTable_conversion(inTable, outLocation, outTable)
    
    
    # Join the TableView to the gdb field based on common field
    currentmessage = ('\tjoining new table data ...\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    #
    inFeatures = "grid_layer"
    joinField = "ref_ROW_COL"
    joinTable = outTable
    joinField2 = dh_layer_dictionary['joinField']
    fieldList = dh_layer_dictionary['fieldList']
    arcpy.JoinField_management(inFeatures, joinField, joinTable, joinField2, fieldList)
    arcpy.Delete_management("grid_layer")
    
    currentmessage = ('\tFinished ArcGIS processing of simulated dh field.\n'
                      + bscut.datetime() + '\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    return
#
