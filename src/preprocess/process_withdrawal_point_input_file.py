# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to jwg (at) srwmd.org

import os

class CreateFilesForCUPProcessing(object):
    """ Python class for reading a comma-delimited ascii file with withdrawal-
        point data and converting it into a form that can be used for subsequent
        processing.
        
        Input file format is as follows:
        
            The first record contains the cup id number and permittee name, with
            a comma separating each value.
                    
            The second record contains the following 'header record':
            
            WellKey,WellId,XCoord,YCoord,layer,Q_cfd

            (Note: old header was station_id,station_name,coord_x,coord_y,withdrawal_rate_mgd)
            
            Subsequent records in the input file correspond to individual
            withdrawal points (i.e. one record per withdrawal point). Each
            record has the following fields (occurring left to right in the
            following order):
            
            field 1: a string or number that uniquely identifies the withdrawal
                     point.
            field 2: a string representing the name of the withdrawal point
            field 3: the horizontal (x) coordinate of the point (assumed to be
                     Florida State Plane North)
            field 4: the vertical (y) coordinate of the point (assumed to be
                     Florida State Plane North)
            field 5: model layer that the withdrawal point withdraws water from
                     Note that if a given withdrawal point withdraws water from
                     multiple model layers, the withdrawal can be represented
                     using two input file records, with each representing their
                     proportion of the total withdrawal from the well (e.g.
                     directly proportional to the relative transmissivities
                     of the two layers)
            field 5: withdrawal rate from the withdrawal point, in millions of
                     gallons per day
                     
            The following is an example input file data record:
            
            123117,Caine Well,2492535.1,321238.622,2,0.1728
            
        2015-06-13 original code Trey Grubbs
        
        Use at your own risk. Please report any errors to jwg@srwmd.org
    """

    def __init__(self, input_file_name,cwd):
        input_file = open(input_file_name, 'r')
        self.cup_id, self.cup_name = tuple(input_file.readline().rstrip().split(',')[:2])
        self.input_header = input_file.readline()
        input_records = [x.rstrip().split(',') for x in input_file.readlines()]
        input_file.close()
        self.output_records, self.sum_cfd, self.sum_mgd = self.create_output_records_and_sums(input_records)

    def create_output_records_and_sums(self, input_records):
        sum_cfd = 0.
        sum_mgd = 0.
        output_records = []
        for record in input_records:
            output_record = record[:-1]
            try:
                rate_mgd = float(record[-1])
                rate_cfd = rate_mgd*1.e6/7.48052
                sum_mgd += rate_mgd
                sum_cfd += rate_cfd
                print(sum_mgd, sum_cfd)
                output_record.append('{0}'.format(rate_cfd))
                output_records.append(output_record)
            except TypeError:
                raise TypeError, "withdrawal rate field doesn't have the proper format"
                error_file = open(os.path.join(cwd,'stop_file.asc'), 'w')
                error_file.write('1\n')
                error_file.close()            
            except:
                raise Exception
                error_file = open(os.path.join(cwd,'stop_file.asc'), 'w')
                error_file.write('1\n')
                error_file.close()            

        return(output_records,sum_cfd,sum_mgd)

    def output_cfd_rates(self, output_file_name):
        """ Output records with rates in cubic feet per day to
            a file.
        """
        output_file = open(output_file_name, 'w')
        self.output_header = self.input_header.rstrip()[:-3] + 'cfd\n'
        output_file.write(self.output_header)
        for record in self.output_records:
            output_string = ','.join(record) + '\n'
            output_file.write(output_string)
        output_file.close()

    def output_total_withdrawal_rate_in_cfd(self, output_file_name):
        """ Output total withdrawal rate to a file. """
        output_file = open(output_file_name, 'w')
        print ("This is where the file is written, cfd, mgd", self.sum_cfd, self.sum_mgd)
        output_string = '{0},{1}\n'.format(self.cup_id,self.sum_mgd)
        print ("This is the string printed:", output_string)
        output_file.write(output_string)
        output_file.close()

def main(in_file,workingdir):
    #cup_id_and_name_input_file_name, withdrawal_point_locations_and_rates_mgd_name = tuple(sys.argv[1:3])
    #cup_id_and_name_input_file_name = 'cup_id_and_name.csv'
    withdrawal_point_locations_and_rates_mgd_name = in_file#'sim_cup_input.csv'
    a = CreateFilesForCUPProcessing(withdrawal_point_locations_and_rates_mgd_name,workingdir)
    output_file_name_1 = os.path.join(workingdir,'withdrawal_point_locations_and_rates.csv')
    output_file_name_2 = os.path.join(workingdir,'cup_id_and_rate.csv')
    a.output_cfd_rates(output_file_name_1)
    a.output_total_withdrawal_rate_in_cfd(output_file_name_2)

    print('Process complete')
    return
#main()

            

