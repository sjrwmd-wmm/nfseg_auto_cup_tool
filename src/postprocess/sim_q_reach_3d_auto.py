#!/usr/bin/python
"""
    The intended use of this program is to extract boundary-condition
    flux data from a MODFLOW listing file and aggregate these simulated fluxes
    for selected river reaches and springs. The program is designed to handle
    multiple (but a limited number of) stress periods.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

    Please report any errors to Trey Grubbs at the Suwannee River Water
    Management District (jwg@srwmd.org).

    change log:

    2014-09-02  jwg    original ('non-PEST') version of program that
                       computed simulated fluxes and compared them
                       to observed values.

    2015-03-08  jwg    modified to only work with simulated values
                       (for PEST).

    2015-07-19  jwg    modified to handle input files where
                       number of bc records could vary from one
                       stress period to the next

    2015-08-24  jwg    program output is now space- (not comma-) delimited
                       add Unix command call at line 1
                       revert back to sys.argv for MODFLOW listing file name input
                       drop fractional change from output file

    2015-09-05  jwg    Program now handles '3-d' River Package features used
                       in NFSEG model (i.e. same river segment in multiple
                       layers) correctly.

    2015-09-06  jwg    unit conversion now applied to del_total_sim_flux
                       (not used by NFSEG, however)

    2015-10-21  jwg    small revisions for use with NFSEG drains (e.g. add
                       'drn' to list of bc types in main(). Also, method,
                       output_gaged_reach_fluxes, in class, GagedReaches,
                       now auto-detects bc types (from parsing of gaged-
                       reach definitions file) - haven't tested this yet,
                       though.

    2015-10-29  jwg    auto-detection of bc types turned off for now.
                       Instead, list of bc_types now added as parameter
                       for method, output_gaged_reach_fluxes, in class,
                       GagedReaches.
                       
    2018-07-25  jwg    reach-id lookup shelf file now called, 
                       lookup_bc_reach_ids_auto.shelf, and now contains
                       stress-period 1 data that are identical to stress
                       period 2 data
    
    20200518   PMB      Reorganized the main program to be a called function
                        from the main python tool running the CUP process.
                        Added arguments to the function call to read from
                        preset definition file locations and write results
                        within the working results directory. Additionally,
                        some of the basic functions have been delegated
                        to the global utilities versions (e.g., delete files).
                        This required adding the PATH to these utilities.
                        Added a logfile that is also sent to the two classes.
                        
                        TODO: Simplify the whole script.
                              Add True/False to return of main

"""

# Import libraries
import time
import shelve
import sys
import os
# Import internal python scripts
from utilities import basic_utilities as bscut


class GagedReaches:
    """ Class for working with gaged-reach data. """
    def __init__(self, reach_definition_file_name, logfile):
        self.define_gaged_reaches_by_2d_reach_ids(reach_definition_file_name)
        #self.number_of_stress_periods = number_of_stress_periods

    def define_gaged_reaches_by_2d_reach_ids(self, reach_definition_file_name):
        """ Read combinations of gaged-reach identifier and boundary-condition
           '2d reach ids' that define each gaged reach. The boundary-condition
            2d reach ids correspond to 2-dimensional GIS feature that has
            corresponding MODFLOW boundary-condition features at the same
            horizontal location (e.g. latitude and longitude), and possibly
            in multiple model layers. Therefore, 2d-reach ids are associated
            with corresponding lists of one or more MODFLOW boundary condition
            features that have the same boundary condition type (e.g. River
            Package) and are collocated horizontally but may occur in multiple
            model layers. This allows for a given segment of a river to be
            represented by multiple MODFLOW River package features, each of
            which have their own unique identifier (their 3-d identifier)
            which are in turn associated with a unique (2-d) identifier that
            identifies the river segment.

            The parameter, reach_definition_file_names, is a string containing
            the name of the file defining the reach associations for MODFLOW
            'list-type' boundary condition (e.g. River, Drain, and GHB Package)
            input-file, stress-period records.

            This method expects comma-delimited records to have the following fields:

            gaged_reach_id:             a string identifying the reach

            bc_type:                    a string indicating the reach type. Currently implmented
                                        bc types include 'drn' (for MODFLOW Drain Package),
                                        'ghb' (for MODFLOW General Head Boundary Package)
                                        'riv' for (MODFLOW River Package)

            bc_id_2d:                   an integer that corresponds to the reach number
                                        in the table of simulated River Package leakage
                                        values reported in the MODFLOW listing file
        """

        self.gaged_reach_list = []
        self.gaged_reach_bc_types = {}
        self.gaged_reach_bc_2d_id_list = {}

        f = open(reach_definition_file_name, 'r')

        for line in f.readlines()[1:]:
            line_list = line.rstrip().split(',')
            #convert bc reach identifiers to integers
            try:
                line_list[2] = int(line_list[2])
            except Exception as exc:
                error_message = ("can't convert {0} to an integer".format(line_list[2]))
                
                with open(logfile,'a') as lf:
                    lf.write(error_message)
                    lf.write('{}\n'.format(exc))
                
                raise Exception(error_message)
            
            
            gaged_reach_id, bc_type, bc_id_2d = tuple(line_list[:3])

            if self.gaged_reach_bc_2d_id_list.has_key((gaged_reach_id, bc_type)):
                if (bc_id_2d in self.gaged_reach_bc_2d_id_list[(gaged_reach_id, bc_type)]) == False:
                    self.gaged_reach_bc_2d_id_list[(gaged_reach_id, bc_type)].append(bc_id_2d)
            else:
                if gaged_reach_id not in self.gaged_reach_list:
                    # first input record for this gaged reach
                    self.gaged_reach_list.append(gaged_reach_id)
                    self.gaged_reach_bc_types[(gaged_reach_id)] = [bc_type]
                else:
                    # first occurrence of this bc_type for this gaged_reach_id
                    self.gaged_reach_bc_types[(gaged_reach_id)].append(bc_type)
                self.gaged_reach_bc_2d_id_list[(gaged_reach_id, bc_type)] = [bc_id_2d]

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

    def calc_gaged_reach_sim_flux(self, bc_reach_fluxes, num_stress_periods, lists_of_3d_ids_from_2d_ids):
        """ Compute simulated flux for each gaged-reach and stress period.
            Assume (for now) that there is only one time step per stress
            period.
        """
        time_step = 1
        self.gaged_reach_sim_fluxes = {}
        for gaged_reach_id in self.gaged_reach_list:
            for bc_type in self.gaged_reach_bc_types[(gaged_reach_id)]:
                for bc_2d_id in self.gaged_reach_bc_2d_id_list[(gaged_reach_id, bc_type)]:
                    for stress_period in range(1,num_stress_periods+1):
                        if bc_type == 'riv':
                            for bc_3d_id in lists_of_3d_ids_from_2d_ids[(bc_type, stress_period)][bc_2d_id]:
                                if gaged_reach_id == '2322700' and bc_type == 'riv' and stress_period == 1:
                                    pass
                                self.update_2d_flux(bc_reach_fluxes,
                                                    gaged_reach_id,
                                                    bc_type, bc_3d_id,
                                                    stress_period,
                                                    time_step)
                        else:
                            bc_3d_id = bc_2d_id
                            self.update_2d_flux(bc_reach_fluxes,
                                                gaged_reach_id,
                                                bc_type, bc_3d_id,
                                                stress_period,
                                                time_step)

    def update_2d_flux(self, bc_reach_fluxes, gaged_reach_id, bc_type, bc_3d_id, stress_period, time_step):
        """ Update simulated flux for a 2d boundary-condition feature group.
        """
        if self.gaged_reach_sim_fluxes.has_key((gaged_reach_id, bc_type, stress_period, time_step)):
            if gaged_reach_id == '2322700' and bc_type == 'riv' and stress_period == 2:
                pass
            try:
                flux = bc_reach_fluxes[(bc_type, bc_3d_id, stress_period, time_step)]
                self.gaged_reach_sim_fluxes[(gaged_reach_id, bc_type, stress_period, time_step)] += flux
            except Exception as exc:
                
                error_message = ("key, ({0},{1},{2},{3}) not found! Halting sim_q_reach.py without writing output.".format(bc_type, bc_3d_id, stress_period, time_step))
                
                with open(logfile,'a') as lf:
                    lf.write(error_message)
                    lf.write('{}\n'.format(exc))
                
                raise Exception(error_message)
                
        else:
            if gaged_reach_id == '2322700' and bc_type == 'riv' and stress_period == 2:
                pass
            try:
                flux = bc_reach_fluxes[(bc_type, bc_3d_id, stress_period, time_step)]
                self.gaged_reach_sim_fluxes[(gaged_reach_id, bc_type, stress_period, time_step)] = flux
            except Exception as exc:
                
                error_message = ("key, ({0},{1},{2},{3}) not found! Halting sim_q_reach.py without writing output.".format(bc_type, bc_3d_id, stress_period, time_step))
                
                with open(logfile,'a') as lf:
                    lf.write(error_message)
                    lf.write('{}\n'.format(exc))
                
                raise Exception(error_message)
                

    def output_gaged_reach_fluxes(self, sim_results_file_name, num_stress_periods, conversion_factor_for_output=1., bc_types=['drn','riv', 'ghb']):
        """ Output simulated and observed fluxes for each gaged reach. """
        time_step = 1
        total_sim_flux = {}
        sim_results_file = self.init_obs_versus_sim_output_file(sim_results_file_name, bc_types, num_stress_periods)
        for gaged_reach_id in self.gaged_reach_list:
            output_string = '{0:>20s}'.format(gaged_reach_id)
            for stress_period in range(1,num_stress_periods+1):
                total_sim_flux[(stress_period, time_step)] = 0
                for bc_type in bc_types:
                    bc_flux = self.assign_bc_flux_for_output(gaged_reach_id, bc_type, stress_period, time_step)
                    total_sim_flux[(stress_period, time_step)] += bc_flux
                    output_string += '      {0: .8e}'.format(bc_flux*conversion_factor_for_output)
                output_string += '      {0: .8e}'.format(total_sim_flux[(stress_period, time_step)]*conversion_factor_for_output)
            if num_stress_periods == 2:
                del_total_sim_flux = total_sim_flux[(2, time_step)] - total_sim_flux[(1, time_step)]
                if abs(total_sim_flux[(1, time_step)]) > 0.:
                    del_total_sim_flux_fraction = del_total_sim_flux/total_sim_flux[(1, time_step)]
                else:
                    del_total_sim_flux_fraction = -1.2345e25
                #output_string += '      {0: .8e}      {1: .8e}\n'.format(del_total_sim_flux,del_total_sim_flux_fraction)
                output_string += '      {0: .8e}\n'.format(del_total_sim_flux*conversion_factor_for_output)
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
        output_string = '{0:>20s}'.format('gaged_reach_id')
        for stress_period in range(1,num_stress_periods+1):
            for bc_type in bc_type_list:
                output_string += ' {0}_sim_flux_sp{1}_ts{2}'.format(bc_type,stress_period,time_step)
            output_string += ' total_sim_flux_sp{0}_ts{1}'.format(stress_period,time_step)
        if num_stress_periods == 2:
            #output_string += ' del_total_sim_flux del_total_sim_flux_fraction\n'
            output_string += ' del_total_sim_flux\n'
        else:
            output_string += '\n'
        sim_results_file.write(output_string)
        return(sim_results_file)


class ModflowListing:

    def __init__(self, modflow_listing_file_name, bc_types, logfile):
        """ Initialize variables and data structures. """
        self.num_stress_periods_in_listing = 0
        self.bc_types = bc_types
        self.bc_reach_list = {}
        self.init_bc_reach_list()
        self.bc_reach_fluxes = {}
        self.openFiles(modflow_listing_file_name)

    def init_bc_reach_list(self):
        """ Initialize the dictionary of bc_reach_ids. """
        for bc_type in self.bc_types:
            self.bc_reach_list[bc_type] = []

    def openFiles(self,modflow_listing_file_name):
        #inFileName = raw_input("Please enter name of MODFLOW input file for parsing: ")
        self.inFile = open(modflow_listing_file_name, 'r')
        #output_file_name = modflow_listing_file_name + '.out.csv'
        #self.outFile = open(output_file_name, 'w')

    def parseListingFile(self, bc_reach_id_dict):
        """ Parse MODFLOW listing file for simulated boundary-condition
            flux values.
        """
        self.bc_reach_id_dict = bc_reach_id_dict
        while 1:
            line = self.inFile.readline()
            if not line:
                break
            self.checkForNewStressPeriod(line)
            if 'drn' in self.bc_types:
                self.checkForDrainFluxBlock(line)
            if 'riv' in self.bc_types:
                self.checkForRiverFluxBlock(line)
            if 'ghb' in self.bc_types:
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
                error_message = ('reached end of file while reading GHB fluxes')
                with open(logfile,'a') as lf: lf.write(error_message)
                raise ValueError(error_message)
            elif line[:9] != ' BOUNDARY':
                break
            bc_reach_seq_num = int(line.rstrip()[10:16])
            bc_reach_id = self.bc_reach_id_dict[('ghb',stress_period)][bc_reach_seq_num-1]
            if stress_period == 1 and time_step == 1:
                self.bc_reach_list['ghb'].append(bc_reach_id)
            flux = float(line.rstrip()[62:])
            self.bc_reach_fluxes[('ghb', bc_reach_id, stress_period, time_step)] = flux

    def parseDrainFluxBlock(self,stress_period,time_step):
        while 1:
            line = self.inFile.readline()
            if not line:
                error_message = ('reached end of file while reading DRAIN fluxes')
                with open(logfile,'a') as lf: lf.write(error_message)
                raise ValueError(error_message)
            elif line[:6] != ' DRAIN':
                break
            bc_reach_seq_num = int(line.rstrip()[7:13])
            bc_reach_id = self.bc_reach_id_dict[('drn',stress_period)][bc_reach_seq_num-1]
            if stress_period == 1 and time_step == 1:
                self.bc_reach_list['drn'].append(bc_reach_id)
            flux = float(line.rstrip()[59:])
            self.bc_reach_fluxes[('drn', bc_reach_id, stress_period, time_step)] = flux

    def parseRiverFluxBlock(self,stress_period,time_step):
        while 1:
            line = self.inFile.readline()
            if not line:
                error_message = ('reached end of file while reading RIVER fluxes')
                with open(logfile,'a') as lf: lf.write(error_message)
                raise ValueError(error_message)
            elif line[:6] != ' REACH':
                break
            bc_reach_seq_num = int(line.rstrip()[7:13])
            bc_reach_id = self.bc_reach_id_dict[('riv',stress_period)][bc_reach_seq_num-1]
            if stress_period == 1 and time_step == 1:
                self.bc_reach_list['riv'].append(bc_reach_id)
                if bc_reach_id > 40951:
                    pass
            flux = float(line.rstrip()[58:])
            self.bc_reach_fluxes[('riv', bc_reach_id, stress_period, time_step)] = flux

    def close_files(self):
        #self.outFile.close()
        pass

def retrieve_id_data_from_lookup_shelf_file(lookup_bc_reach_id_shelf_file_name):
    """ Open 'shelf' files with:

            (1) lists that provide a way for looking up a
            boundary-condition reach id if you know the order that that reach id
            appears in the MODFLOW output listing of simulated fluxes for a given
            boundary-condition type (e.g. River Package, GHB Package, etc.).

            (2) dict with lists of 3d bc ids for a given 2d bc id
    """
    bc_id_dict = {}
    book = shelve.open(lookup_bc_reach_id_shelf_file_name)
    bc_id_dict['lists_of_3d_ids_by_bc_type_and_stress_period'] = book['reach_ids']
    bc_id_dict['lists_of_3d_ids_from_2d_ids'] = book['reach_ids_from_2d_ids']
    book.close()
    return(bc_id_dict)


def main(listfile,
         conversion_factor_for_output_in,
         logfile,
         postproc_deffiles_dQ,
         postproc_dQ_results_dir,
         gaged_reach_flux_out):
    """ Compute simulated 'gaged-reach' fluxes by extract simulated drn, ghb,
        and riv fluxes from MODFLOW output listing. Compare them with observed
        values and output results to a file.
    """
    
    
    start_time = time.time()
    modflow_listing_file_name = listfile

    #modflow_listing_file_name = 'nfseg.lst'
    #modflow_listing_file_name = raw_input("Please enter name of modflow listing file to be processed: ")

    #bc_types = sys.argvi[2]
    bc_types = ['drn','riv', 'ghb']
    #lookup_bc_reach_id_shelf_file_name = sys.argv[3]
    lookup_bc_reach_id_shelf_file_name = os.path.join(postproc_deffiles_dQ,'lookup_bc_reach_ids_auto.shelf')
    bc_id_dict = retrieve_id_data_from_lookup_shelf_file(lookup_bc_reach_id_shelf_file_name)

    modflow_input_format = 'free'
    #output_file = open('gaged_reach_fluxes.csv', 'w')

    # parse the MODFLOW listing file
    mf = ModflowListing(modflow_listing_file_name, bc_types, logfile)
    mf.parseListingFile(bc_id_dict['lists_of_3d_ids_by_bc_type_and_stress_period'])

    # shelve results for further postprocessing if second command-line argument is present
    #debug_shelf_file_name = 'temp.shelf'
    if True:
    #if len(sys.argv) > 1:
        #hydro_feature_sim_fluxes_shelve_file_name = sys.argv[2]
        hydro_feature_sim_fluxes_shelve_file_name = os.path.join(postproc_dQ_results_dir,'bc_fluxes.shelve')
        bscut.deletefile(hydro_feature_sim_fluxes_shelve_file_name,logfile)
        # Commented out as part of organization of input files !!! PMB !!! 20200518
        #if os.path.exists(os.path.join(os.getcwd(),hydro_feature_sim_fluxes_shelve_file_name)):
        #    os.remove(os.path.join(os.getcwd(),hydro_feature_sim_fluxes_shelve_file_name))
        book = shelve.open(hydro_feature_sim_fluxes_shelve_file_name)
        book['bc_fluxes'] = mf.bc_reach_fluxes
        book['bc_list'] = mf.bc_reach_list
        book.close()

    # compute the simulated gaged-reach fluxes
    gaged_reaches = GagedReaches(os.path.join(postproc_deffiles_dQ,'gaged_reach_definitions.csv'), logfile)
    gaged_reaches.calc_gaged_reach_sim_flux(mf.bc_reach_fluxes,
                                            mf.num_stress_periods_in_listing,
                                            bc_id_dict['lists_of_3d_ids_from_2d_ids'])

    
    # Output to file
    conversion_factor_for_output = conversion_factor_for_output_in
    try:
        conversion_factor_for_output = float(conversion_factor_for_output)
        gaged_reaches.output_gaged_reach_fluxes(gaged_reach_flux_out,
                                                mf.num_stress_periods_in_listing,
                                                conversion_factor_for_output,
                                                bc_types)
    except Exception as exc:
        error_message = ("problem converting conversion factor {0}. Are you sure it's a float?\n\n".format(conversion_factor_for_output))
        
        with open(logfile,'a') as lf:
            lf.write(error_message)
            lf.write('{}\n'.format(exc))
        
        raise Exception(error_message)
    # End try-except
    
    mf.close_files()
    elapsed_time = time.time() - start_time
    
    currentmessage = ('\tProcess complete\n\tGaged-reach post-processing executed in {0:0.1f} seconds.'.format(elapsed_time))
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    return

#main()
