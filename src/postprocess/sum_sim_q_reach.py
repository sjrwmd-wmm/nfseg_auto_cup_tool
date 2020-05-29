#!/usr/bin/python
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Please report errors and corrections to Trey Grubbs (jwg (at) srwmd.org)

   change log:
       20150512 Trey Grubbs original code
       20150825 Trey Grubbs update output headers, change output file names
                            program now expects spaces-delimited data in gaged-reach input


        20150905 Trey Grubbs code now makes no assumptions about units of input data
        
        20150906 Trey Grubbs append change in total flux to list of field names in
                             output file header.
                             
        20150907 Trey Grubbs throw an exception and don't write an output file if
                             input file does not exist.
        
        20200518   PMB  Reorganized the main program to be a called function
                        from the main python tool running the CUP process.
                        Added arguments to the function call to read from
                        preset definition file locations and write results
                        within the working results directory.
                        Added a logfile that is written to.
                        
                        TODO: Simplify the whole script.
                              Add True/False to return of main

"""


import os

class ContributingGages(object):
    """ Class for defining and working with relations between gaging stations
        and their upstream contributing gaging stations.
        
        20150512 Trey Grubbs original code
        
        20150905 Trey Grubbs code now makes no assumptions about units of input data
        
        20150906 Trey Grubbs append change in total flux to list of field names in
                             output file header.
                             
        20160317 Trey Grubbs fix output header (it didn't include ghb fluxes and the
                             ordering of riv and drn fluxes were reversed). Doesn't
                             affect .ins file, however.
    """
    
    def __init__(self):
        pass

    def initialize_output_files(self,output_file_name):
        """ Open output files. """
        #output_file_name = 'gaged_fluxes_sum.csv'

        output_file_header = 'station_id,station_name,drn_sim_flux_sp1,riv_sim_flux_sp1,ghb_sim_flux_sp1,total_sim_flux_sp1,drn_sim_flux_sp2,riv_sim_flux_sp2,ghb_sim_flux_sp2,total_sim_flux_sp2,total_sim_flux_sp2_minus_sp1\n'
        self.output_file = open(output_file_name, 'w')
        self.output_file.write(output_file_header)

    def parse_upstream_gage_numbers(self, input_file_name):
        """ Parse a file containing a list of gages that contribute flow to a
            downstream gage.
        """
        self.station_list = []
        self.station_name_from_station_id = {}

        self.upstream_station_ids = {}
        f = open(input_file_name, 'r')
        for line in f.readlines():
            line_list = line.rstrip().split(',')
            ds_station_id = line_list[0]
            ds_station_name = line_list[1]
            #us_station_ids = [int(x) for x in line_list[1:]]
            us_station_ids = line_list[2:]
            us_station_ids.append(ds_station_id)
            self.upstream_station_ids[ds_station_id] = us_station_ids
            self.station_list.append(ds_station_id)
            self.station_name_from_station_id[ds_station_id] = ds_station_name
        f.close()

    def parse_simualted_deltaQ(self, input_file_name):
        """ Parse a file containing a list of gages that contribute flow to 
            a downstream gage of interest.
        """
        self.sim_delta_bc_fluxes = {}
        self.sim_delta_bc_flux_field_indices = {}
        f = open(input_file_name, 'r')
        
        self.sim_delta_bc_flux_fields = f.readline().rstrip().split()[1:]
        for field_name in self.sim_delta_bc_flux_fields:
            index_value = self.sim_delta_bc_flux_fields.index(field_name)
            self.sim_delta_bc_flux_field_indices[field_name] = index_value
            
        for line in f.readlines():
            line_list = line.rstrip().split()
            ds_station_id = line_list[0]
            flux_tuple = [float(x) for x in line_list[1:]]
            self.sim_delta_bc_fluxes[ds_station_id] = flux_tuple
        f.close()

    def cumulate_fluxes(self):
        """ Cumulate fluxes from upstream, contributing river reaches. """
        self.cum_bc_fluxes = {}
        for station_id in self.station_list:
            if station_id == 2321500:
                pass
            for upstream_station_id in self.upstream_station_ids[station_id]:
                for flux_type in self.sim_delta_bc_flux_fields:
                    flux_type_index = self.sim_delta_bc_flux_field_indices[flux_type]
                    this_key = (station_id, flux_type)
                    this_flux = self.sim_delta_bc_fluxes[upstream_station_id][flux_type_index]
                    if self.cum_bc_fluxes.has_key(this_key):
                        self.cum_bc_fluxes[this_key] += this_flux
                    else:
                        self.cum_bc_fluxes[this_key] = this_flux
                    test_in = self.cum_bc_fluxes[this_key]
            self.output_cumulative_sim_bc_fluxes(station_id)
    
    def output_cumulative_sim_bc_fluxes(self, station_id):
        """ Output cumulative flux data for each station. """
        output_record = self.create_output_string(station_id)
        self.output_file.write(output_record)

    def create_output_string(self, station_id):
        """ Assemble output strings for a given station number. """
        output_string = '{0},{1}'.format(station_id, self.station_name_from_station_id[station_id])
        for flux_type in self.sim_delta_bc_flux_fields:
            flux_value = self.cum_bc_fluxes[(station_id, flux_type)]
            output_string += ',{0:06f}'.format(flux_value)
        output_string += '\n'
        return output_string

    def close_output_files(self):
        """ Close the output files. """
        self.output_file.close()

def main(logfile,
         postproc_deffiles_dQ,
         simulated_delta_bc_fluxes_file_name,
         gaged_flux_sum_output):
    
    """ Main program. """
    #upstream_gage_numbers_file_name = 'upstream_gage_numbers.csv'
    #simulated_delta_bc_fluxes_file_name = 'gaged_reach_fluxes.asc'
    #gaged_flux_sum_output = 'gaged_fluxes_sum.csv'
    
    # Setup the PATH and name of a definition file
    upstream_gage_numbers_file_name = os.path.join(postproc_deffiles_dQ,'upstream_gage_numbers.csv')
    
    #if os.path.exists(os.path.join(os.getcwd(),simulated_delta_bc_fluxes_file_name)):
    if os.path.exists(simulated_delta_bc_fluxes_file_name):
        a = ContributingGages()
        a.initialize_output_files(gaged_flux_sum_output)
        a.parse_upstream_gage_numbers(upstream_gage_numbers_file_name)
        a.parse_simualted_deltaQ(simulated_delta_bc_fluxes_file_name)
        a.cumulate_fluxes()
        a.close_output_files()
        
        currentmessage = ('Finished computing cumulative river fluxes!\n\n')
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write(currentmessage)
    else:
        error_message = ("File, {0}, does not exist! Halting execution of sum_sim_q_reach.py\n".format(simulated_delta_bc_fluxes_file_name))
        
        with open(logfile,'a') as lf: lf.write(error_message)
        
        raise Exception(error_message)
        
    
    return

#main()
