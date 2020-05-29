# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to jwg (at) srwmd.org

class ContributingGages(object):
    """ Class for defining and working with relations between gaging stations
        and their upstream contributing gaging stations.
        
        20150512    original code   Trey Grubbs
        20180725    gaged-reach fluxes input file now expected to be in space(s)-delimited format   Trey Grubbs
                    gaged-id's now processed as string types
    """
    
    def __init__(self):
        pass

    def initialize_output_files(self):
        """ Open output files. """
        output_summary_file_name = 'delta_q_summary.csv'
        output_details_file_name = 'delta_q_details.csv'

        output_summary_file_header = 'station_number,station_name,simulated_flux_base_condition_cfs,simulated_flux_with_cup_cfs,simulated_change_in_flow_cfs,simulated_percent_change_in_flow,simulated_change_in_flow_as_a_fraction_of_cup\n'
        output_details_file_header = 'station_number,station_name,riv_sim_flux_sp1_ts1,drn_sim_flux_sp1_ts1,total_sim_flux_sp1_ts1,riv_sim_flux_sp2_ts1,drn_sim_flux_sp2_ts1,total_sim_flux_sp2_ts1,del_total_sim_flux,del_total_sim_flux_fraction\n'

        self.output_summary_file = open(output_summary_file_name, 'w')
        self.output_details_file = open(output_details_file_name, 'w')

        self.output_summary_file.write(output_summary_file_header)
        self.output_details_file.write(output_details_file_header)

    def read_file_with_cup_id_and_amount(self, input_file_name):
        """ Parse a file containing one record and two-fields:
                cup id number
                withdrawal rate, in 
            Store the data in instance variables.
        """
        f = open(input_file_name, 'r')
        line_list = f.readline().rstrip().split(',')
        self.cup_id, self.cup_withdrawal_mgd = tuple(line_list)
        self.cup_withdrawal_mgd = float(self.cup_withdrawal_mgd)
        self.cup_withdrawal_cfs = self.cup_withdrawal_mgd * 1.e6 / (7.48052 * 86400.)

    def parse_station_numbers_and_names_file(self, input_file_name):
        """ Parse a file containing two-fields: station number and station name.
            Store the data in a dictionary.
        """
        self.station_list = []
        self.station_name_from_station_number = {}
        f = open(input_file_name, 'r')
        for line in f.readlines():
            line_list = line.rstrip().split(',')
            station_number, station_name = tuple(line_list)
            station_number = station_number
            self.station_list.append(station_number)
            self.station_name_from_station_number[station_number] = station_name
        f.close()

    def parse_upstream_gage_numbers(self, input_file_name):
        """ Parse a file containing a list of gages that contribute flow to a
            downstream gage.
        """
        self.upstream_station_numbers = {}
        f = open(input_file_name, 'r')
        for line in f.readlines():
            line_list = line.rstrip().split(',')
            ds_station_number = line_list[0]
            us_station_numbers = [x for x in line_list[2:]]
            if ds_station_number == '2319500':
                pass
            self.upstream_station_numbers[ds_station_number] = us_station_numbers
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
            ds_station_number = line_list[0]
            flux_tuple = [float(x) for x in line_list[1:]]
            self.sim_delta_bc_fluxes[ds_station_number] = flux_tuple
        f.close()

    def cumulate_fluxes(self):
        """ Cumulate fluxes from upstream, contributing river reaches. """
        self.cum_bc_fluxes = {}
        for station_number in self.station_list:
            if station_number == 2321500:
                pass
            for upstream_station_number in self.upstream_station_numbers[station_number]:
                for flux_type in self.sim_delta_bc_flux_fields:
                    flux_type_index = self.sim_delta_bc_flux_field_indices[flux_type]
                    this_key_cfd = (station_number, flux_type, 'cfd')
                    this_key_cfs = (station_number, flux_type, 'cfs')
                    this_flux = self.sim_delta_bc_fluxes[upstream_station_number][flux_type_index]
                    if self.cum_bc_fluxes.has_key(this_key_cfd):
                        self.cum_bc_fluxes[this_key_cfd] += this_flux
                    else:
                        self.cum_bc_fluxes[(this_key_cfd)] = this_flux
                    test_in = self.cum_bc_fluxes[(this_key_cfd)]
                    self.cum_bc_fluxes[(this_key_cfs)] = self.cum_bc_fluxes[(this_key_cfd)]/86400.
                    test_out = self.cum_bc_fluxes[(this_key_cfs)]
            self.output_cumulative_sim_bc_fluxes(station_number)
    
    def output_cumulative_sim_bc_fluxes(self, station_number):
        """ Output cumulative flux data for each station. """
        output_record_detailed = self.create_output_string_detailed(station_number)
        output_record_summary = self.create_output_string_summary(station_number)
        self.output_summary_file.write(output_record_summary)
        self.output_details_file.write(output_record_detailed)

    def create_output_string_detailed(self, station_number):
        """ Assemble output strings for a given station number. """
        output_string_cfd = '{0},{1}'.format(station_number, self.station_name_from_station_number[station_number])
        output_string_cfs = ''
        for flux_type in self.sim_delta_bc_flux_fields:
            flux_value_cfs = self.cum_bc_fluxes[(station_number, flux_type, 'cfs')]
            flux_value_cfd = self.cum_bc_fluxes[(station_number, flux_type, 'cfd')]
            output_string_cfd += ',{0:06f}'.format(flux_value_cfd)
            output_string_cfs += ',{0:06f}'.format(flux_value_cfs)
        total_flux_fraction_of_cup = self.cum_bc_fluxes[(station_number, 'del_total_sim_flux', 'cfs')]/self.cup_withdrawal_cfs
        output_string = output_string_cfd + output_string_cfs
        output_string += ',{0:06f}\n'.format(total_flux_fraction_of_cup)
        return output_string

    def create_output_string_summary(self,station_number):
        """ Assemble output strings for a given station number. """
        output_string = '{0},{1},'.format(station_number, self.station_name_from_station_number[station_number])
        flux_sp1 = self.cum_bc_fluxes[(station_number,'total_sim_flux_sp1_ts1', 'cfs')]
        flux_sp2 = self.cum_bc_fluxes[(station_number,'total_sim_flux_sp2_ts1', 'cfs')]
        flux_change = self.cum_bc_fluxes[(station_number,'del_total_sim_flux', 'cfs')]
        if abs(flux_sp1) > 1.e-10:
            flux_percent_change = 100.*flux_change/flux_sp1
        else:
            flux_percent_change = -1.2345e30
        flux_change_fraction_of_cup = flux_change/self.cup_withdrawal_cfs
        output_tuple_for_appending = (flux_sp1, flux_sp2, flux_change, flux_percent_change, flux_change_fraction_of_cup)
        output_list_for_joining = ['{0}'.format(x) for x in output_tuple_for_appending]
        output_string_for_appending = ','.join(output_list_for_joining)
        output_string += (output_string_for_appending + '\n')
        return output_string

    def close_output_files(self):
        """ Close the output files. """
        self.output_details_file.close()
        self.output_summary_file.close()

def main():
    """ Main program. """
    cup_id_and_rate_file_name = 'cup_id_and_rate.csv'
    station_number_and_names_file_name = 'station_number_and_names.csv'
    upstream_gage_numbers_file_name = 'upstream_gage_numbers.csv'
    simulated_delta_bc_fluxes_file_name = 'gaged_reach_fluxes.asc'
    
    a = ContributingGages()
    a.read_file_with_cup_id_and_amount(cup_id_and_rate_file_name)
    a.initialize_output_files()
    a.parse_station_numbers_and_names_file(station_number_and_names_file_name)
    a.parse_upstream_gage_numbers(upstream_gage_numbers_file_name)
    a.parse_simualted_deltaQ(simulated_delta_bc_fluxes_file_name)
    a.cumulate_fluxes()
    a.close_output_files()
    
    print('All Done!')

main()
