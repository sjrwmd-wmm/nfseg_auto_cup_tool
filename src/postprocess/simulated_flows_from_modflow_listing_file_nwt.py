# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to jwg (at) srwmd.org

"""
    The intended use of this program is to extract boundary-condition
    flux data from a MODFLOW listing file and aggregate these simulated fluxes
    for selected river reaches and springs. The program is designed to handle
    multiple (but a limited number of) stress periods.
    
    2018-07-24 update to read redirected input file from sys.argv   Trey Grubbs
"""

import time
import shelve
import sys

class GagedReaches:
    """ Class for working with gaged-reach data. """
    def __init__(self, reach_definition_file_name):
        self.define_gaged_reaches_by_bc_reach_indices(reach_definition_file_name)

    def define_gaged_reaches_by_bc_reach_indices(self, reach_definition_file_name):
        """ Read combinations of gaged-reach identifier and boundary-condition
           'reach indeces' that define each gaged reach. The boundary-condition
            reach indices correspond to to from MODFLOW listing file) data that define each gaged reach.
        
            The parameter, reach_definition_file_names, is a string containing
            the name of the file defining the reach associations for River Package
            Drain Package records.
            This method expects comma-delimited records to have the following fields:
            
            gaged_reach_id:             a string identifying the reach
            bc_type:                    a string indicating the reach type. Currently implmented
                                        bc types include 'drn' (for MODFLOW Drain Package),
                                        'ghb' (for MODFLOW General Head Boundary Package)
                                        'riv' for (MODFLOW River Package)
            bc_reach_id:                an integer that corresponds to the reach number
                                        in the table of simulated River Package leakage
                                        values reported in the MODFLOW listing file
            
            There will also be a comma-delimited record that is not read by this program.
        """

        self.gaged_reach_list = []
        self.gaged_reach_bc_reach_types = {}
        self.gaged_reach_bc_reach_list = {}

        f = open(reach_definition_file_name, 'r')

        for line in f.readlines()[1:]:
            line_list = line.rstrip().split(',')
            # convert bc reach identifiers to integers
            line_list[2] = int(line_list[2])
            gaged_reach_id, bc_reach_id, bc_type = tuple(line_list)
            if self.gaged_reach_bc_reach_list.has_key((gaged_reach_id, bc_type)):
                if (bc_reach_id in self.gaged_reach_bc_reach_list[(gaged_reach_id, bc_type)]) == False:
                    self.gaged_reach_bc_reach_list[(gaged_reach_id, bc_type)].append(bc_reach_id)
            else:
                if gaged_reach_id not in self.gaged_reach_list:
                    # first input record for this gaged reach
                    self.gaged_reach_list.append(gaged_reach_id)
                    self.gaged_reach_bc_reach_types[(gaged_reach_id)] = [bc_type]
                else:
                    # first occurrence of this bc_type for this gaged_reach_id
                    self.gaged_reach_bc_reach_types[(gaged_reach_id)].append(bc_type)
                self.gaged_reach_bc_reach_list[(gaged_reach_id, bc_type)] = [bc_reach_id]

        f.close()

    def assign_observations_to_reaches(self, reach_observations_file_name):
        """ Read a file containing observed values for each reach.
        
            This file is specified in the input parameter, reach_observations_file_name.
            It is expected to be in ASCII, comma-delimited format, and to contain two
            fields: gaged_reach_id (a string) and observed_value (a float).
        """
        self.gaged_reach_observations = {}
        f = open(reach_observations_file_name, 'r')
        # dictionary contain a list of grid-cells that constitute each gaged-reach
        for line in f.readlines():
            line_list = line.rstrip().split(',')
            gaged_reach_id, observed_value = tuple(line_list)
            observed_value = float(observed_value)
            self.gaged_reach_observations[gaged_reach_id] = observed_value
        f.close()

    def calc_gaged_reach_sim_flux(self, bc_reach_fluxes, num_stress_periods):
        """ Compute simulated flux for each gaged-reach and stress period.
            Assume (for now) that there is only one time step per stress
            period.
        """
        time_step = 1
        self.gaged_reach_sim_fluxes = {}
        for gaged_reach_id in self.gaged_reach_list:
            for bc_type in self.gaged_reach_bc_reach_types[(gaged_reach_id)]:
                for bc_reach_id in self.gaged_reach_bc_reach_list[(gaged_reach_id, bc_type)]:
                    for stress_period in range(1,num_stress_periods+1):
                        if self.gaged_reach_sim_fluxes.has_key((gaged_reach_id, bc_type, stress_period, time_step)):
                            flux = bc_reach_fluxes[(bc_type, bc_reach_id, stress_period, time_step)]
                            self.gaged_reach_sim_fluxes[(gaged_reach_id, bc_type, stress_period, time_step)] += flux
                        else:
                            flux = bc_reach_fluxes[(bc_type, bc_reach_id, stress_period, time_step)]
                            self.gaged_reach_sim_fluxes[(gaged_reach_id, bc_type, stress_period, time_step)] = flux
                            #self.gaged_reach_sim_fluxes[(gaged_reach_id, bc_type)] = bc_reach_fluxes[(bc_type, bc_reach_id, stress_period, time_step)]
                            #                                                   self.bc_reach_fluxes[(  'drn', bc_reach_id, stress_period, time_step)] = flux
                            

    def output_gaged_reach_fluxes(self, sim_results_file_name, num_stress_periods):
        """ Output simulated and observed fluxes for each gaged reach. """
        time_step = 1
        bc_type_list = ['riv','drn']
        total_sim_flux = {}
        sim_results_file = self.init_obs_versus_sim_output_file(sim_results_file_name, bc_type_list, num_stress_periods)
        for gaged_reach_id in self.gaged_reach_list:
            output_string = '{0}'.format(gaged_reach_id)
            for stress_period in range(1,num_stress_periods+1):
                total_sim_flux[(stress_period, time_step)] = 0
                for bc_type in bc_type_list:
                    bc_flux = self.assign_bc_flux_for_output(gaged_reach_id, bc_type, stress_period, time_step)
                    total_sim_flux[(stress_period, time_step)] += bc_flux
                    output_string += ',{0:.8e}'.format(bc_flux)
                output_string += ',{0:.8e}'.format(total_sim_flux[(stress_period, time_step)])
            if num_stress_periods == 2:
                del_total_sim_flux = total_sim_flux[(2, time_step)] - total_sim_flux[(1, time_step)]
                if abs(total_sim_flux[(1, time_step)]) > 0.:
                    del_total_sim_flux_fraction = del_total_sim_flux/total_sim_flux[(1, time_step)]
                else:
                    del_total_sim_flux_fraction = -1.2345e25
                output_string += ',{0:.8e},{1:.8e}\n'.format(del_total_sim_flux,del_total_sim_flux_fraction)
            else:
                output_string += '\n'
            sim_results_file.write(output_string)
        sim_results_file.close()

    def assign_bc_flux_for_output(self, gaged_reach_id, bc_type, stress_period, time_step):
        """ Retrieve bc flux for a given
            gaged-reach id, bc_type, stress period, and time step.
        """
        if self.gaged_reach_sim_fluxes.has_key((gaged_reach_id, bc_type, stress_period, time_step)):
            bc_flux = self.gaged_reach_sim_fluxes[(gaged_reach_id, bc_type, stress_period, time_step)]
        else:
            bc_flux = 0.
        return(bc_flux)        

    def init_obs_versus_sim_output_file(self, sim_results_file_name, bc_type_list, num_stress_periods):
        """ Open an output file with simulated versus observed flux data, and
            write a header with field names to that file.
        """
        time_step = 1
        sim_results_file = open(sim_results_file_name, 'w')
        output_string = 'gaged_reach_id'
        for stress_period in range(1,num_stress_periods+1):
            for bc_type in bc_type_list:
                output_string += ',{0}_sim_flux_sp{1}_ts{2}'.format(bc_type,stress_period,time_step)
            output_string += ',total_sim_flux_sp{0}_ts{1}'.format(stress_period,time_step)
        if num_stress_periods == 2:
            output_string += ',del_total_sim_flux,del_total_sim_flux_fraction\n'
        else:
            output_string += '\n'
        sim_results_file.write(output_string)
        return(sim_results_file)
        
        
class ModflowListing:

    def __init__(self, modflow_listing_file_name):
        """ Initialize variables and data structures. """
        self.num_stress_periods_in_listing = 0
        bc_types = ['riv', 'drn', 'ghb']
        self.bc_reach_list = {}
        self.init_bc_reach_list(bc_types)
        self.bc_reach_fluxes = {}
        self.openFiles(modflow_listing_file_name)

    def init_bc_reach_list(self, bc_types):
        """ Initialize the dictionary of bc_reach_ids. """
        for bc_type in bc_types:
            self.bc_reach_list[bc_type] = []
        
    def openFiles(self,modflow_listing_file_name):
        #inFileName = raw_input("Please enter name of MODFLOW input file for parsing: ")
        self.inFile = open(modflow_listing_file_name, 'r')
        output_file_name = modflow_listing_file_name + '.out.csv'
        self.outFile = open(output_file_name, 'w')

    def parseListingFile(self):
        while 1:
            line = self.inFile.readline()
            if not line:
                break
            self.checkForNewStressPeriod(line)
            self.checkForDrainFluxBlock(line)
            self.checkForRiverFluxBlock(line)
            self.checkForGHBFluxBlock(line)
        self.inFile.close()        

    def checkForNewStressPeriod(self, line):
        """ Check to see if this is the beginning of the listing of information
            for a new stress period.
        """
        if line[:45] == '                            STRESS PERIOD NO.':
            self.num_stress_periods_in_listing += 1
            self.stress_period = int(line[46:50])            
            
    def checkForGHBFluxBlock(self,line):
        if line.find("  HEAD DEP BOUNDS   PERIOD") == 0:
            stress_period = int(line.rstrip()[27:31])
            time_step = int(line.rstrip()[39:42])
            self.parseGHBFluxBlock(stress_period,time_step) 

    def checkForDrainFluxBlock(self,line):
        if line.find("           DRAINS   PERIOD") == 0:
            stress_period = int(line.rstrip()[27:31])
            time_step = int(line.rstrip()[38:42])
            self.parseDrainFluxBlock(stress_period,time_step)

    def checkForRiverFluxBlock(self,line):
        if line.find("    RIVER LEAKAGE   PERIOD") == 0:
            stress_period = int(line.rstrip()[27:31])
            time_step = int(line.rstrip()[38:42])
            self.parseRiverFluxBlock(stress_period,time_step)

    def parseGHBFluxBlock(self,stress_period,time_step):
        while 1:
            line = self.inFile.readline()
            if not line:
                raise ValueError, 'reached end of file while reading drain fluxes'
            elif line[:9] != ' BOUNDARY':
                break
            bc_reach_id = int(line.rstrip()[10:16])
            if stress_period == 1 and time_step == 1:
                self.bc_reach_list['ghb'].append(bc_reach_id)
            flux = float(line.rstrip()[62:])
            self.bc_reach_fluxes[('ghb', bc_reach_id, stress_period, time_step)] = flux

    def parseDrainFluxBlock(self,stress_period,time_step):
        while 1:
            line = self.inFile.readline()
            if not line:
                raise ValueError, 'reached end of file while reading drain fluxes'
            elif line[:6] != ' DRAIN':
                break
            bc_reach_id = int(line.rstrip()[7:13])
            if stress_period == 1 and time_step == 1:
                self.bc_reach_list['drn'].append(bc_reach_id)
            flux = float(line.rstrip()[59:])
            self.bc_reach_fluxes[('drn', bc_reach_id, stress_period, time_step)] = flux

    def parseRiverFluxBlock(self,stress_period,time_step):
        while 1:
            line = self.inFile.readline()
            if not line:
                raise ValueError, 'reached end of file while reading river fluxes'
            elif line[:6] != ' REACH':
                break
            bc_reach_id = int(line.rstrip()[7:13])
            if stress_period == 1 and time_step == 1:
                self.bc_reach_list['riv'].append(bc_reach_id)
                if bc_reach_id > 40951:
                    pass
            flux = float(line.rstrip()[58:])
            self.bc_reach_fluxes[('riv', bc_reach_id, stress_period, time_step)] = flux

    def close_files(self):
        self.outFile.close()

def main():
    """ Compute simulated 'gaged-reach' fluxes by extract simulated drn, ghb,
        and riv fluxes from MODFLOW output listing. Compare them with observed
        values and output results to a file.
    """
    start_time = time.time()
    modflow_listing_file_name = sys.argv[1]
    #modflow_listing_file_name = 'test.lst'
    #modflow_listing_file_name = raw_input("Please enter name of modflow listing file to be processed: ")

    modflow_input_format = 'free'
    #output_file = open('gaged_reach_fluxes.csv', 'w')    

    # parse the MODFLOW listing file
    mf = ModflowListing(modflow_listing_file_name)
    mf.parseListingFile()

    # shelve results for debugging
    book = shelve.open('temp.shelf')
    book['bc_reach_fluxes'] = mf.bc_reach_fluxes
    book['bc_reach_list'] = mf.bc_reach_list
    book.close()

    # compute the simulated gaged-reach fluxes
    gaged_reaches = GagedReaches('gaged_reach_definitions.csv')
    gaged_reaches.calc_gaged_reach_sim_flux(mf.bc_reach_fluxes, mf.num_stress_periods_in_listing)
    gaged_reaches.output_gaged_reach_fluxes('gaged_reach_fluxes.csv',mf.num_stress_periods_in_listing)

    mf.close_files()
    elapsed_time = time.time() - start_time
    print('\nAll Done!\n\nGaged-reach post-processing program executed in {0:0.1f} seconds.'.format(elapsed_time))

main()
