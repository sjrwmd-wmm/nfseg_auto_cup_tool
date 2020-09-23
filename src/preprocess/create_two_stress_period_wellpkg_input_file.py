# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to jwg (at) srwmd.org

#import shutil
#import sys
import os

class WellPkgInputFile(object):
    """ This is a Python class for parsing and updating MODFLOW-200x Well Package
        input files.
        
        original code by Trey Grubbs 2014-12-12
        Use at your own risk.
        Please contact Trey Grubbs, jwg@srwmd.org, if any errors are found.
    """

    def __init__(self, new_injection_wells = False):
        """ Initialize class """
        self.new_injection_wells = new_injection_wells

    def parse_header(self, header_file_name):
        """ Extract information from the Well Package input file header. Note
            that the program expects the header to contain data for a one
            stress period simulation. Note that the input data are expected to
            either be free-format or have a leading space.
        """
        header_file = open(header_file_name, 'r')
        lines = header_file.readlines()
        self.comment_and_parameter_flag_lines = lines[:-1]
        max_active_wells, well_cbc_unit = tuple(lines[-1].rstrip().split())
        self.max_active_wells = int(max_active_wells)
        self.well_cbc_unit = int(well_cbc_unit)
        header_file.close()

    def parse_stress_period(self, stress_period_file_name):
        """ Extract stress-period 1 data from the Well Package input file. """
        stress_period_file = open(stress_period_file_name, 'r')        
        line = stress_period_file.readline()
        #self.num_records_sp1, self.number_of_parameters_sp1 = tuple([int(item) for item in line.rstrip().split()])
        self.num_records_sp1 = int(line.strip().split()[0])
        self.number_of_parameters_sp1 = 0
        self.data_records_sp1 = stress_period_file.readlines()
        stress_period_file.close()
   
    def parse_new_wells_input_file(self, new_wells_file_name):
        """ Parse a .csv file with containing layer, row, column, and
            withdrawal rate data for new wells to be added to the
            stress-period 1 dataset.
        """
        new_wells_file = open(new_wells_file_name, 'r')
        lines = new_wells_file.readlines()
        header = lines[0].rstrip().split(',')
        header_lookup = self.parse_new_wells_file_header(header)
        self.parse_new_wells_file_withdrawal_records(lines[1:], header_lookup)
        new_wells_file.close()

    def parse_new_wells_file_header(self, input_list):
        """ Return a dictionary with the list index values for
            each element in the input list.
        """
        output_dict = {}
        current_index = 0
        for item in input_list:
            output_dict[item] = current_index
            current_index += 1
        return(output_dict)

    def parse_new_wells_file_withdrawal_records(self, line_list, index_lookup):
        """ Parse data records in new wells file. """
        self.new_wells_records = []
        for this_line in line_list:
            this_line_list = this_line.rstrip().split(',')
            layer = this_line_list[index_lookup['LAYER']]
            row = this_line_list[index_lookup['ROW']]
            column = this_line_list[index_lookup['COL']]
            q = float(this_line_list[index_lookup['Q_CFD']])
            if not self.new_injection_wells:
                q = -1.*q
            #outline = "{0:>10}{1:>10}{2:>10}{3:10.1f}\n".format(layer, row, column, q) # !!! PMB Changed format 20200310
            outline = "{0:>10}{1:>11}{2:>11}{3:>17.7g}\n".format(layer, row, column, q)
            self.new_wells_records.append(outline)

    def update_max_active_wells(self):
        """ Update the maximum number of active wells. """
        self.max_active_wells += len(self.new_wells_records)
    
    def create_two_stress_period_input_file(self, outfile_name):
        """ Create a two-stress period Well Package input file
            by copying the data from stress period 1 and appending
            the new withdrawal points.
        """
        output_file = open(outfile_name, 'w')
        output_file.writelines(self.comment_and_parameter_flag_lines)
        output_file.write("{0:>10}{1:>10}\n".format(self.max_active_wells, self.well_cbc_unit))
        output_file.write("{0:>10}{1:>10}\n".format(self.num_records_sp1, self.number_of_parameters_sp1))
        output_file.writelines(self.data_records_sp1)
        output_file.write("{0:>10}{1:>10}\n".format(self.max_active_wells, self.number_of_parameters_sp1))       
        output_file.writelines(self.data_records_sp1)
        output_file.writelines(self.new_wells_records)
        output_file.close()

def main(output_file_name, workingdir, logfile):
    """ Program for creating a two-stress period Well Package input file, by:
            (1) reading an existing Well Package input file with one stress
                period,
            (2) reading a .csv file with containing layer, row, column, and
                withdrawal rate data for new wells that are to be added to
                the wells represented in (1)
            (3) output a two-stress period Well Package input file.
            
            Use at your own risk.
            Please contact Trey Grubbs, jwg@srwmd.org, if any errors are found.

    """
    ##output_file_name = 'nfseg.wel'
    #output_file_name = sys.argv[1]
    wellpkg = WellPkgInputFile(new_injection_wells = False)
    wellpkg.parse_header(os.path.join(workingdir,'wellpkg_header_nfseg.asc'))
    wellpkg.parse_stress_period(os.path.join(workingdir,'wellpkg_stress_period_01_records_nfseg.asc'))
    wellpkg.parse_new_wells_input_file(os.path.join(workingdir,'wells_to_add.csv'))
    wellpkg.update_max_active_wells()
    wellpkg.create_two_stress_period_input_file(output_file_name)
    
    currentmessage = ('\tCreated new Well Package input file\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    return
#main()

        
        
        
