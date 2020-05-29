# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to jwg (at) srwmd.org

class BudgetChangeSummaryTable:
    """ Class for computing sum of River and Drain Package flux changes that
        were output by the program test.py.
        
        2015-06-15 changed name of output file             Trey Grubbs
        2018-07-24 program now incorporates ghb fluxes
                   and output file has .asc suffix         Trey Grubbs

        Please use at your own risk and report any
        any errors to Trey Grubbs (jwg@srwmd.org).
        
        20200518    Paul Bremner    -Reorganization to make this a function
                                     of a larger python script.
                                    -Added the main function.
                                    -Added output to the logfile.
                                    -Input/output files now supplied through
                                     arguments
                                    
                                    TODO: Add True/False to return of main
                                          Simplify the whole script

    """   
    def __init__(self,input_file_name,outfile):
        """ Open the input and output files. """
        #input_file_name = raw_input("\tReceiving name of input file: ")
        self.in_file = open(input_file_name, 'r')
        #self.out_file = open('global_river_plus_drain_flux_changes.asc', 'w')
        self.out_file = open(outfile, 'w')
        

    def read_summary_table(self):
        """ Read the data from the input file and store in a list. """
        self.header_list = self.in_file.readline().rstrip().split(',')
        self.data_records = [line.rstrip().split(',') for line in self.in_file.readlines()]

    def parse_data_records(self):
        """ Parse the data that was stored in list, data_records, storing the essential
            data in the dict, data_dict.
        """
        self.data_dict = {}
        for record in self.data_records:
            self.data_dict[(record[0], record[1], 'net_rate_sp2_minus_sp1')] = float(record[14])
            self.data_dict[(record[0], record[1], 'fraction_of_well_pkg')] = float(record[15])

    def calc_summary(self):
        """ Calcualte the sum of river and drain package flux changes. """
        riv_plus_drn_plus_ghb_cfs = self.data_dict[('RIVER LEAKAGE', 'cfs', 'net_rate_sp2_minus_sp1')] + \
                           self.data_dict[('DRAINS', 'cfs', 'net_rate_sp2_minus_sp1')] + \
                           self.data_dict[('HEAD DEP BOUNDS', 'cfs', 'net_rate_sp2_minus_sp1')]
        riv_plus_drn_plus_ghb_mgd = self.data_dict[('RIVER LEAKAGE', 'mgd', 'net_rate_sp2_minus_sp1')] + \
                           self.data_dict[('DRAINS', 'mgd', 'net_rate_sp2_minus_sp1')] + \
                           self.data_dict[('HEAD DEP BOUNDS', 'mgd', 'net_rate_sp2_minus_sp1')]
        riv_plus_drn_plus_ghb_fraction = riv_plus_drn_plus_ghb_cfs / self.data_dict[('WELLS', 'cfs', 'net_rate_sp2_minus_sp1')]
        return(riv_plus_drn_plus_ghb_cfs, riv_plus_drn_plus_ghb_mgd, riv_plus_drn_plus_ghb_fraction)

    def output_results(self, summary_tuple):
        """ Write sum of river and drain package flux changes to an output file. """
        riv_plus_drn_plus_ghb_cfs, riv_plus_drn_plus_ghb_mgd, riv_plus_drn_plus_ghb_fraction = summary_tuple
        self.out_file.write('river + drain + ghb flux change, in cfs: %0.4f\n' % (riv_plus_drn_plus_ghb_cfs))
        self.out_file.write('river + drain + ghb flux change, in mgd: %0.4f\n' % (riv_plus_drn_plus_ghb_mgd))
        self.out_file.write('river + drain + ghb flux change, as a fraction of change in well pkg flux: %0.4f\n' % (riv_plus_drn_plus_ghb_fraction))        

    def close_files(self):
        self.in_file.close()
        self.out_file.close()

def main(rivfluxin,outfile,logfile):
    """ Compute the sum of River, Drain, and GHB Package flux changes and output results to a file. """
    tbl = BudgetChangeSummaryTable(rivfluxin,outfile)
    tbl.read_summary_table()
    tbl.parse_data_records()
    summary_tuple = tbl.calc_summary()
    tbl.output_results(summary_tuple)
    tbl.close_files()
    currentmessage = ('\n\tProcess complete')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    return

#main()
