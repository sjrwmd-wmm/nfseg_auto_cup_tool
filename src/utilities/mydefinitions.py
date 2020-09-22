#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Please report errors and corrections to pbremner (at) sjrwmd.com
#
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

import os
import time


# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Unit Conversion Factors
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

class ConvFactors:
    def __init__(self):
        
        # Convert from day to seconds
        # 24.0[hr/day]*3600.0[sec/hr] = 86400.0[sec/day]
        self.day2sec = 86400.0
        
        # Convert from seconds to days
        # 1.0 / day2sec = 1.0 / 86400.0[sec/day] = ~1.5e-5[day/sec]
        #self.sec2day = 1.1574074074074073e-05 # improved accuracy value
        #self.sec2day = 1.0 / self.day2sec # improved accuracy value, and calculates at machine precision
        self.sec2day = 1.157407407E-05 # tmp (previous) value
        
        # Convert US Gallon to cubic inches
        # Convert US Gallon to cubic feet
        # US Gallon is defined as 231 cubic inches ~ 3.785 liters
        # gallon to cubic inches to cubic feet ~ 0.13368055555555555 [ft^3]
        self.gal2ci = 231.0
        self.gal2cf = self.gal2ci/(pow(12.0,3.0))
        #
        # Convert cubic inches to US Gallon
        # Convert cubic feet to US Gallon
        # gallon to cubic inches to cubic feet ~ 7.48051948051948 [gal]
        self.ci2gal = 1.0/self.gal2ci
        self.cf2gal = (pow(12.0,3.0))*self.ci2gal
        
        # Conversion from gallons per day (gd) and per second (gs)
        # to cubic feet per day (cfd) and per second (cfs), respectively.
        # [US] units
        # gd to cfd = gal per day * gal2cf ~ 0.13368055555555556 [cfd]
        # 77.0 / 576.0  exact form from Wolfram
        self.gd2cfd = 0.13368055419447 # Tmp version until testing is done
        #self.gd2cfd = self.gal2cf # Most accurate version
        self.gs2cfs = self.gal2cf # Most accurate version
        
        
        # Conversion from million gallons per day (mgd)
        # to cubic feet per day (cfd). [US] units
        # mgd to cfd = 1.0e6 gal per day * gal2cf ~ 133680.55555555556 [cfd]
        self.mgd2cfd = 133680.55419447 # Tmp version until testing is done
        #self.mgd2cfd = 1.0e6 * self.gd2cfd # Most accurate version
        #
        #
        # Conversion from cubic feet day (cfd)
        # to million gallons per day (mgd). [US] units
        # cfd to mgd = 1 cfd * cf2gal * 1.0e-6 ~ 7.48051948051948e-06 [mgd]
        self.cfd2mgd = 0.0000074805195567 # Tmp version until testing is done
        #self.cfd2mgd = self.cf2gal/(1.0e6) # Most accurate version
        
        
        # Conversion from million gallons per day (mgd)
        # to cubic feet per second (cfs). [US] units
        # mgd to cfs = 1 mgd * 1.0e6 * gal2cf / day2sec ~ 1.5472286522633745 [cfs]
        self.mgd2cfs = 1.e6 / (7.48052 * 86400.)  # Trey's approximation -- meant for comparing to old output only
        #self.mgd2cfs = 1.5472286365101; # Version using more decimal values
        #self.mgd2cfs = (1.0e6 * self.gal2cf) / self.day2sec # Most accurate version
        #
        #
        # Conversion from cubic feet per second (cfs)
        # to million gallons per day (mgd). [US] units
        # cfs to mgd = 1 cfs * cf2gal * day2sec / 1.0e6 ~ 0.6463168831168831 [mgd]
        self.cfs2mgd = 0.64631688969744 # Tmp until testing is done
        #self.cfs2mgd = (self.cf2gal * self.day2sec) / 1.0e6 # Most accurate version
        
# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Introduction Banners -- Runtime and Logfile
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def introbanner():    
    print ('=========================================================================\n' +
           '            NFSEG AUTOMATED WATER-USE PERMIT SIMULATION TOOL\n\n' +
           '    This is the main script used to evaluate the impact of adding\n' +
           '    new wells to the NFSEG model.\n\n' +
           '    This script is designed to read a user supplied csv file\n' +
           '    containing the id, location, and withdrawal rate of the wells\n' +
           '    requesting a permit.\n\n' +
           '    New wells are processed utilizing MODFLOW. Results are\n' +
           '    summarized in two csv files and an updated mxd. The log and\n' +
           '    output files are written to a new results directory.\n' +
           '        1. <results>\<user_input_filename>_delta_q_summary.csv\n' +
           '        2. <results>\<user_input_filename>_global_budget_change.csv\n' +
           '        3. <results>\gis\dh.mxd\n\n' +
           '    For questions contact:\n' +
           '                  PMBremner - pbremner@sjrwmd.com\n' +
           '                  LMeridth  - lmeridth@sjrwmd.com\n' +
           '                  DDurden   - Douglas.Durden@srwmd.org\n' +
           '=========================================================================\n\n')
    return

def logbanner():
    dt = ('\tRun datetime: {0}\n'.format(time.asctime(time.localtime())))
    logbanner = ('\n\n' +
              'xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox\n\n' +
              '        --  NFSEG AUTOMATED WATER-USE PERMIT SIMULATION TOOL  --\n\n' +
              '        --                     LOG OUTPUT                     --\n\n' +
              dt +
              'xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox\n\n\n')
    
    return logbanner
# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Exit Poems
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def print_poem(option):
    
    if (option==1):
        poem = ('\tShake hands, we shall never be friends, all\'s over;\n' +
                '\tI only vex you the more I try.\n' +
                '\tAll\'s wrong that ever I\'ve done or said,\n' +
                '\tAnd nought to help it in this dull head:\n' +
                '\tShake hands, here\'s luck, good-bye.\n\n' +
                '\tBut if you come to a road where danger\n' +
                '\tOr guilt or anguish or shame\'s to share,\n' +
                '\tBe good to the lad that loves you true\n' +
                '\tAnd the soul that was born to die for you,\n' +
                '\tAnd whistle and I\'ll be there.\n\n' +
                '\tA. E. Housman (1859-1936)\n' +
                '\tShake hands, we shall never be friends, all\'s over\n\n')
    elif (option==2):
        poem = ('\tSince there\'s no help, come let us kiss and part.\n' +
                '\tNay, I have done, you get no more of me;\n' +
                '\tAnd I am glad, yea glad with all my heart,\n' +
                '\tThat thus so cleanly I myself can free.\n' +
                '\tShake hands for ever, cancel all our vows,\n' +
                '\tAnd when we meet at any time again,\n' +
                '\tBe it not seen in either of our brows\n' +
                '\tThat we one jot of former love retain.\n' +
                '\tNow at the last gasp of Love\'s latest breath,\n' +
                '\tWhen, his pulse failing, Passion speechless lies;\n' +
                '\tWhen Faith is kneeling by his bed of death,\n' +
                '\tAnd Innocence is closing up his eyes-\n' +
                '\tNow, if thou wouldst, when all have given him over,\n' +
                '\tFrom death to life thou might\'st him yet recover!\n\n' +
                '\tMichael Drayton, 1594\n' +
                '\tSince there\'s no help, come let us kiss and part\n\n')
    # end if
    
    return poem
# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# List of Error Codes or Strings to Look For
# When Error Checking
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

class ErrorListValues:
    def __init__(self):
        # Start a list of Error Keywords to be on the lookout for
        self.ErrorList = ['error','Error','ERROR'
                          ,'infinity','Infinity','INFINITY'
                          ,'overflow','Overflow','OVERFLOW'
                          ,'exception','Exception','EXCEPTION'
                          ,'divide by zero'
                          ,'segmentation fault','Segmentation fault'
                          ,'Segmentation Fault','SEGMENTATION FAULT'
                          ,'SIGSEGV'
                          ,"Can't find"]
# ooooooooooooooooooooooooooooooooooooooooooooooooooooo


# TODO: move these to basic_utilities
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# File Existance Check
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def checkfileexist(file_name):
    if not os.path.isfile(file_name):
        error_message = ('\nERROR:\tThe file, ' +
                         file_name +
                         ', does not exist!\n\n' +
                         '\tPlease try again . . .\n\n')
        raise ValueError(error_message)
    #if not os.path.exists(file_name):
        #error_message = ('\n\n\nERROR:\tThe file, ' +
                         #file_name +
                         #', does not exist!\n\n' +
                         #'\tPlease try again . . .\n\n')
        #raise ValueError(error_message)
    
    return
# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Projection Check
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
def projcheck(proj,projlist):
    if proj not in projlist:
        error_message = ('\n\n\n\tOh no ... something went wrong\n\n' +
                         '\tERROR:\tUser supplied Projection, ' + proj + ', is incorrect, please try again.\n\n' +
                         '\tOptions are 1=SRWMD or 2=SJRWMD.\n\n' +
                         '\tCode Usage:    When prompted input the well input_file_name,\n' +
                         '\t               And when prompted again, input SRWMD or SJRWMD\n' +
                         '\t               ***or input 1 or 2***\n' +
                         '\t               to correspond to the map projection used to\n' +
                         '\t               make the input well csv file.\n\n' +
                         '\t... This program must now end ....\n\n\n' +
                         print_poem(1))
        raise ValueError(error_message)
    
    return
# ooooooooooooooooooooooooooooooooooooooooooooooooooooo
