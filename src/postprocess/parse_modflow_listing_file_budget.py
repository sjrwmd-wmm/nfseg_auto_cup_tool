# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to jwg (at) srwmd.org

""" Code for extracting global budget info from MODFLOW-NWT listing file.

    2014-08-08 original code                           Trey Grubbs
    2015-05-16 small changes to work with MODFLOW-NWT  Trey Grubbs
    2015-06-15 changed name of output file             Trey Grubbs
    2015-06-22 fixed column names in output file       Trey Grubbs

    Code is provided as is. Use at your own risk and report any
    any errors to Trey Grubbs (jwg@srwmd.org).
"""

import copy

class ModflowListing:

    def __init__(self):
        self.budget_items = {}
        self.budget_differences = {}
        self.activeFluxTerms = {}
        self.extracted_rates = {}

    def openFiles(self,inFileName,outFileName):
        #inFileName = raw_input("\tReceiving name of MODFLOW input file for parsing: ")
        self.inFile = open(inFileName, 'r')
        ##outFileName = inFileName + '.out.csv'
        #outFileName = 'global_budget_change.csv'
        self.outFile = open(outFileName, 'w')
    
    def parseListingFile(self):
        while 1:
            line = self.inFile.readline()
            if not line:
                break
            self.checkForBudgetBlock(line)
        
    def checkForBudgetBlock(self,line):
        if line.find("  VOLUMETRIC BUDGET FOR ENTIRE MODEL AT END OF TIME STEP") == 0:
            stress_period = int(line.rstrip()[-3:])
            time_step = int(line.rstrip()[58:61])
            self.activeFluxTerms[(time_step, stress_period)] = set()
            self.scan_for_flow_block(time_step, stress_period)

    def scan_for_flow_block(self, time_step, stress_period):
        while 1:
            line = self.inFile.readline()
            if not line:
                break
            elif line[10:14] == ' IN:':
                self.parse_budget_sub_block("in", time_step, stress_period)
                self.parse_in_or_out_totals("in", time_step, stress_period)
            elif line[10:14] == 'OUT:':
                self.parse_budget_sub_block("out", time_step, stress_period)
                self.parse_in_or_out_totals("out", time_step, stress_period)
                break

    def parse_budget_sub_block(self, in_or_out, time_step, stress_period):
        """ Parse an inflow or outflow budget sub-block. """
        #skip the first (blank) line in budget sub-block
        line = self.inFile.readline()
        while 1:
            line = self.inFile.readline()
            if line == '\n':
                break
            else:
                line_budget_items = self.parse_budget_line(line, in_or_out, time_step, stress_period)
                self.store_budget_items(line_budget_items, in_or_out, time_step, stress_period)

    def parse_budget_line(self, line, in_or_out, time_step, stress_period):
        """ Parse one line of a budget sub-block. """
        flux_cum_type = line[:20].strip()
        flux_cum_value = float(line[22:39])
        flux_rate_type = line[39:61].strip()
        flux_rate_value = float(line[64:80])
        self.upDate_list_of_active_flux_terms(flux_rate_type, time_step, stress_period)
        return (flux_cum_type, flux_cum_value, flux_rate_type, flux_rate_value)

    def upDate_list_of_active_flux_terms(self, flux_rate_type, time_step, stress_period):
        """ Add flux type to list of active flux terms for this time-step and
            stress period.
        """
        if flux_rate_type in self.activeFluxTerms[(time_step, stress_period)]:
            pass
        else:
            self.activeFluxTerms[(time_step, stress_period)].add(flux_rate_type)

    def store_budget_items(self, line_budget_items, in_or_out, time_step, stress_period):
        """ Store budget items in a dictionary. """
        flux_cum_type, flux_cum_value, flux_rate_type, flux_rate_value = line_budget_items
        self.budget_items[(time_step, stress_period, in_or_out, 'cum', flux_cum_type)] = flux_cum_value
        self.budget_items[(time_step, stress_period, in_or_out, 'rate', flux_rate_type)] = flux_rate_value

    def parse_in_or_out_totals(self, in_or_out, time_step, stress_period):
        """ Parse budget totals record for this time step. """
        line = self.inFile.readline()
        flux_cum_value = float(line[24:39])
        flux_rate_value = float(line[64:80])
        self.budget_items[(time_step, stress_period, in_or_out, 'total_flux_cum')] = flux_cum_value
        self.budget_items[(time_step, stress_period, in_or_out, 'total_flux_rate')] = flux_rate_value

    def compute_sp_diff(self, t1, t2):
        """ Compute inter-stress period differences for all budget components.
            Input: 
                   t1 is a tuple of (time_step, stress_period) for the earlier time step
                   t2 is a tuple of (time_step, stress_period) for the earlier time step
            """
        for budget_term_type in self.activeFluxTerms[(t1[0], t1[1])]:
            in_tuple, out_tuple, net_tuple = self.compute_sp_term_diff(t1, t2, budget_term_type)
            #self.write_sp_rate_record(t1, t2, budget_term_type, in_tuple, out_tuple, net_tuple)
            self.extracted_rates[(t1, t2, budget_term_type)] = (in_tuple, out_tuple, net_tuple)

    def compute_sp_term_diff(self, t1, t2, budget_term_type):
        """ Compute inter-stress period differences for an individual budget component. """
        in_tuple = self.extract_budget_values_for_diff(t1, t2, 'in', 'rate', budget_term_type)
        out_tuple = self.extract_budget_values_for_diff(t1, t2, 'out', 'rate', budget_term_type)
        net_1 = in_tuple[0] - out_tuple[0]
        net_2 = in_tuple[1] - out_tuple[1]
        net_diff = net_2 - net_1
        net_tuple = (net_1, net_2, net_diff)
        return(in_tuple, out_tuple, net_tuple)

    def extract_budget_values_for_diff(self, t1, t2, in_or_out, rate_or_cum, budget_term_type):
        """ Retrieve budget values for difference calcs. """
        q1 = self.budget_items[(t1[0], t1[1], in_or_out, rate_or_cum, budget_term_type)]
        q2 = self.budget_items[(t2[0], t2[1], in_or_out, rate_or_cum, budget_term_type)]
        diff = q2 - q1
        return (q1, q2, diff)

    def write_sp_rate_record(self, t1, t2, budget_term_type, in_tuple, out_tuple, net_tuple):
        """ Format a substring of data for output of difference data. """
        output_string = '%3s,%3s,%3s,%3s,%20s' % (t1[0], t1[1], t2[0], t2[1], budget_term_type)
        in_string = '%16.04f,%16.04f,%16.04f' % in_tuple
        out_string = '%16.04f,%16.04f,%16.04f' % out_tuple
        net_string = '%16.04f,%16.04f,%16.04f' % net_tuple
        output_string = output_string + ',' + ','.join([in_string, out_string, net_string]) + '\n'
        self.outFile.write(output_string)

    def outputResults(self, t1, t2):
        """ write results to output file. """
        self.outputHeader()
        self.outputDataRecords(t1, t2)

    def outputHeader(self):
        """ write field names at beginning of output file. """
        headerList = ['bc_flux_type','flux_units',
                      'timeStep_1','stressPeriod_1',
                      'timeStep_2','stressPeriod_2',
                      'in_rate_1','in_rate_2','in_rate_2_minus_1',
                      'out_rate_1','out_rate_2','out_rate_2_minus_1',
                      'net_rate_1','net_rate_2','net_rate_2_minus_1',
                      'net_rate_2_minus_1_fraction_of_netWellPkg']
        outString = ','.join(headerList)
        self.outFile.write(outString + '\n')

    def outputDataRecords(self, t1, t2):
        sortedFluxTypes = list(copy.deepcopy(self.activeFluxTerms[(t1[0], t1[1])]))
        sortedFluxTypes.sort()
        wellPkg_net = self.extracted_rates[(t1, t2, 'WELLS')][2][2]
        for units_and_conversion in [('cfd',1.),('cfs',1./86400.),('mgd',7.48052/1.e6)]:
            for budget_term_type in sortedFluxTypes:
                in_tuple, out_tuple, net_tuple = self.extracted_rates[(t1, t2, budget_term_type)]
                self.convertThenOutputDataRecord(wellPkg_net, units_and_conversion, t1, t2, budget_term_type, in_tuple, out_tuple, net_tuple)

    def convertThenOutputDataRecord(self, wellPkg_net, units_and_conversion, t1, t2, budget_term_type, in_tuple, out_tuple, net_tuple):
        """ output a data record for this combination of simulation times and budget term type. """
        # convert to appropriate system of units
        outputUnits = units_and_conversion[0]
        convertedTupleList = []
        conversionMultiplier = units_and_conversion[1]
        fractionOfWellPkgNet = net_tuple[2] / wellPkg_net
        for tempTuple in [in_tuple, out_tuple, net_tuple]:
            tempList = []
            for fluxTerm in tempTuple:
                tempList.append(fluxTerm * conversionMultiplier)
            tupleToAppend = tuple(tempList)
            convertedTupleList.append(tupleToAppend)
        convertedTuples = tuple(convertedTupleList)
        # output results
        self.outputRecord(outputUnits, t1, t2, budget_term_type, convertedTuples, fractionOfWellPkgNet)
        
    def outputRecord(self, outputUnits, t1, t2, budget_term_type, convertedTuples, fractionOfWellPkgNet):
        """ Format a substring of data for output of difference data. """
        in_tuple, out_tuple, net_tuple = convertedTuples
        output_string = '%s,%3s,%3s,%3s,%3s,%3s' % (budget_term_type, outputUnits, t1[0], t1[1], t2[0], t2[1])
        if outputUnits == 'cfd':
            formatString = '%16f,%16f,%16f'
        else:
            formatString = '%0.4f,%0.4f,%0.4f'
        in_string = formatString % in_tuple
        out_string = formatString % out_tuple
        net_string = formatString % net_tuple
        fraction_string = '%0.2f' % (fractionOfWellPkgNet,)
        output_string = output_string + ',' + ','.join([in_string, out_string, net_string, fraction_string]) + '\n'
        self.outFile.write(output_string)

    def assign_diff_values(self, t1, t2, budget_term_type, in_tuple, out_tuple, net_tuple):        
        self.budget_differences[(t1, t2, budget_term_type, 'in')] = in_tuple[2]
        self.budget_differences[(t1, t2, budget_term_type, 'out')] = in_tuple[2]
        self.budget_differences[(t1, t2, budget_term_type, 'net')] = net_2 - net_1
        self.write_sp_diff_record(self, t1, t2, in_or_out, rate_or_cum, budget_term_type, flux_tuple)

    def write_sp_diff_record(self, t1, t2, in_or_out, rate_or_cum, budget_term_type, flux_tuple):
        """ Format a substring of data for output of difference data. """
        output_string = '%3s,%3s,%3s,%3s' % (t1[0], t1[1], t2[0], t2[1])
        in_string = '%16.04f,%16.04f,%16.04f' % (flux_tuple[0])
        out_string = '%16.04f,%16.04f,%16.04f' % (flux_tuple[1])
        net_string = '%16.04f,%16.04f,%16.04f' % (flux_tuple[2])
        output_string = output_string + ',' + ','.join(in_string, out_string, net_string) + '\n'
        self.outFile.write(output_string)
        
    def close_files(self):
        self.inFile.close()
        self.outFile.close()

def main(listfile,outfile,logfile):
    a = ModflowListing()
    a.openFiles(listfile,outfile)
    a.parseListingFile()
    a.compute_sp_diff((1, 1), (1, 2))
    a.outputResults((1, 1), (1, 2))    
    a.close_files()
    currentmessage = ('\n\tProcess complete')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    return

#main()
