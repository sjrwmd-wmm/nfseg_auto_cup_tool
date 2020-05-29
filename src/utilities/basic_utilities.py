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
import shutil
import time
import subprocess
#from contextlib import contextmanager  # for setting up cd()
#import glob

import mydefinitions as mydef
#import text_blocks_and_errors as mytxterr


# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Safely change the working directory
# Based on the StackOverflow answer (viewed 20200320):
# https://stackoverflow.com/questions/431684/how-do-i-change-the-working-directory-in-python
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

#@contextmanager
#def cd(newdir):
    #prevdir = os.getcwd()
    #os.chdir(os.path.expanuser(newdir))
    #try:
        #yield
    #finally:
        #os.chdir(prevdir)

def cd(newdir):
    prevdir = os.getcwd()
    
    try:
        os.chdir(os.path.expanduser(newdir))
    except OSError as OS_Error:
        error_message = ('\n\n\nERROR:\tThe directory,\n' +
                        newdir +
                        ',\n\tdoes not exist!\n\n')
        raise OSError(error_message)
        #print (OS_Error)
        # Move onto the next iteration
        #continue
    else:
        pass
    return

# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Print the current date and time
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def datetime():
    #print ('\n- - -\n')
    dt = ('\t***\tCurrent datetime is {0}\t***'.format(time.asctime(time.localtime())))
    #print ('\n- - -\n')
    return dt

# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Delete files if they exist
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def deletefile(file_name,logfile):
    if os.path.isfile(file_name):
        currentmessage = ('Deleting: ' + file_name + '\n')
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write('{}\n'.format(currentmessage))
        os.remove(file_name)
    else:
        currentmessage = ('Nothing to delete: ' + file_name + '\n')
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write('{}\n'.format(currentmessage))
    return

# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Copy files if they exist
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def copyfile(file_in,file_out,logfile):
    
    try:
        # First check if it exists
        mydef.checkfileexist(file_in)
    except ValueError as VError:
        #raise
        with open(logfile,'a') as lf: lf.write('{}'.format(VError))
        return False
    else:
        try:
            shutil.copy2 (file_in, file_out)
            #raise IOError(error_message)
        except IOError as IOErr:
            error_message = ('\nERROR:\tThe file, ' +
                            file_in +
                            ', does not exist.\n\tNo file to copy!\n\n')
            #raise IOError(error_message)
            with open(logfile,'a') as lf:
                lf.write(error_message)
                lf.write('{}\n'.format(IOErr))
            
            return False
        except Exception as exc:
            #raise
            with open(logfile,'a') as lf: lf.write('{}'.format(exc))
            return False
    return True

# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Run Modflow Process
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def modflow(code_dir,model_dir,nam_file,logfile):
    
    # Setup the full PATH to the executable
    exe = os.path.join(code_dir,'MODFLOW-NWT_64.exe')
    
    # Change the working directory to where all the model
    # files are located, then run MODFLOW.
    # Change back when done.
    prevdir = os.getcwd()
    cd(model_dir)
    
    errlist = mydef.ErrorListValues()
    
    try:
        # Define the executable process
        # The [] contains: [executable, option_arg_1, option_arg_2, etc.]
        p = subprocess.Popen([exe,nam_file],
                                stdout = subprocess.PIPE,
                                stdin = subprocess.PIPE,
                                stderr = subprocess.PIPE)
        
        # Execute the code with any command-line arguments
        # Syntax: p.communicate(stdin)
        # Returns a tuple (stdoutdata, stderrdata)
        standardout, standarderror = p.communicate()
        
        # Raise an exception if an error occurs
        #   - Check for error keywords
        #   - Check the subprocess returncode
        #   - Check if any output was given to stderr
        error_flag = False
        for erritem in errlist.ErrorList:
            stdoutindex = standardout.find(erritem)
            stderrindex = standardout.find(erritem)
            #print ('Stdoutindex {}; Stderrindex {}\n'.format(stdoutindex,stderrindex))
            if (stdoutindex != -1 or stderrindex != -1):
                error_flag=True
                break
            # END if
        # END for over erritem
        if (p.returncode != 0 or standarderror or error_flag):
            currentmessage= ('ERROR:\t' +
                             'There was a problem running MODFLOW!\n' +
                             '\tBelow is the report:\n' +
                             'Error code: {}\n'.format(p.returncode) +
                             'Standard Out:\n{}\n'.format(standardout))
            with open(logfile,'a') as lf: lf.write(currentmessage)
            error_message = standarderror
            raise ValueError(error_message)
    except ValueError as VError:
        #raise
        with open(logfile,'a') as lf: lf.write('{}'.format(VError))
        return False
    else: # All went well. Print output and move on
        print ('{}\n'.format(standardout))
        with open(logfile,'a') as lf: lf.write('{}\n'.format(standardout))
    # END try
    
    cd(prevdir)
    
    return True

# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Run PEST Process many2one
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def many2one(code_dir, file_in, many2one_log, results_dir, logfile):
    # !!! LEFT HERE !!! PMB
    # !!! SEPARATE FILES INTO HERE AND TWOARRAY !!! READ FROM INFILE TO DETERMINE FILES TO DELETE !!!
    # !!! HANDLE ERROR CHECKING AND RETURN !!!
    
    currentmessage = ('\n\n\t--- Deleting preexisting output files prior to processing ---\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    #layer1_simHeads_sp1 = os.path.join(postproc_dh_cwd,'layer1_simHeads_sp1.asc')
    #layer3_simHeads_sp1 = os.path.join(postproc_dh_cwd,'layer3_simHeads_sp1.asc')
    #layer1_simHeads_sp2 = os.path.join(postproc_dh_cwd,'layer1_simHeads_sp2.asc')
    #layer3_simHeads_sp2 = os.path.join(postproc_dh_cwd,'layer3_simHeads_sp2.asc')
#    deletefile(layer1_simHeads_sp1,logfile)
#    deletefile(layer3_simHeads_sp1,logfile)
#    deletefile(layer1_simHeads_sp2,logfile)
#    deletefile(layer3_simHeads_sp2,logfile)
    
    # Input file format
    #--------
    #L0  nfseg_auto.hds
    #L1  f
    #L2  y
    #L3  layer1_simHeads_sp1.asc
    #L4  f
    #L5  n
    #L6  y
    #L7  layer3_simHeads_sp1.asc
    #L8  f
    #L9  n
    #L10 n
    #L11 n
    #L12 n
    #L13 y
    #L14 layer1_simHeads_sp2.asc
    #L15 f
    #L16 n
    #L17 y
    #L18 layer3_simHeads_sp2.asc
    #--------
    # Read the output filenames from the input file
    # Proceed with deleting preexisting output files that will be recreated
    with open(file_in,'r') as fin:
        for i,line in enumerate(fin):
            if (i==3 or i==7 or i==14 or i==18):
                outfile = os.path.join(results_dir,line.rstrip())
                deletefile(outfile,logfile)
            #
        #
    #
    
    
    # Change the working directory to where all the model
    # files are located, then run many2one.
    # Change back when done.
    prevdir = os.getcwd()
    cd(results_dir)
    
    
    # Setup the full PATH to the executable
    exe = os.path.join(code_dir,'many2one.exe')
    
    errlist = mydef.ErrorListValues()
    
    try:
        # Define the executable process
        # The [] contains: [executable, option_arg_1, option_arg_2, etc.]
        p = subprocess.Popen([exe,file_in],
                             stdout = subprocess.PIPE,
                             stdin = subprocess.PIPE,
                             stderr = subprocess.PIPE)
        
        
        # Execute the code with any command-line arguments
        # Syntax: p.communicate(stdin)
        # Returns a tuple (stdoutdata, stderrdata)
        standardout, standarderror = p.communicate()
        
        # Raise an exception if an error occurs
        #   - Check for error keywords
        #   - Check the subprocess returncode
        #   - Check if any output was given to stderr
        error_flag = False
        for erritem in errlist.ErrorList:
            stdoutindex = standardout.find(erritem)
            stderrindex = standardout.find(erritem)
            #print ('Stdoutindex {}; Stderrindex {}\n'.format(stdoutindex,stderrindex))
            if (stdoutindex != -1 or stderrindex != -1):
                error_flag=True
                break
            # END if
        # END for over erritem
        if (p.returncode != 0 or standarderror or error_flag):
            currentmessage= ('ERROR:\t' +
                             'There was a problem running the ' +
                             'PEST utility many2one!\n' +
                             '\tBelow is the report:\n' +
                             'Error code: {}\n'.format(p.returncode) +
                             'Standard Out:\n{}\n'.format(standardout))
            with open(logfile,'a') as lf: lf.write(currentmessage)
            error_message = standarderror
            raise ValueError(error_message)
    except ValueError as VError:
        #raise
        with open(logfile,'a') as lf: lf.write('{}'.format(VError))
        return False
    else: # All went well. Write the output to the logfiles and move on
        with open(many2one_log,'w') as fout:
            fout.write('{}\n'.format(standardout))
        #
        with open(logfile,'a') as lf: lf.write('{}\n'.format(standardout))
    # END try
    
    cd(prevdir)
    
    return True

# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Run PEST Process twoarray
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def twoarray(code_dir, file_in, twoarraylog, results_dir, logfile):
    # !!! LEFT HERE !!! PMB
    # !!! HANDLE ERROR CHECKING AND RETURN !!!
    
    currentmessage = ('\n\n\t--- Deleting preexisting output files prior to processing ---\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    #dh_lyr1 = os.path.join(postproc_dh_cwd,'dh_lyr1.asc')
    #dh_lyr3 = os.path.join(postproc_dh_cwd,'dh_lyr3.asc')
    
    # Delete files that will be created again, if they exist
    #deletefile(dh_lyr1,logfile)
    #deletefile(dh_lyr3,logfile)
    
    # EX. Input file format
    #--------
    #L0  model_ft.spc
    #L1  layer1_simHeads_sp2.asc
    #L2  f
    #L3  
    #L4  layer1_simHeads_sp1.asc
    #L5  f
    #L6  
    #L7  s
    #L8  dh_lyr1.asc
    #L9  f
    #--------
    # Read the output filenames from the input file
    # Proceed with deleting preexisting output files that will be recreated
    with open(file_in,'r') as fin:
        for i,line in enumerate(fin):
            if (i==8):
                outfile = os.path.join(results_dir,line.rstrip())
                deletefile(outfile,logfile)
            #
        #
    #
    
    
    # Change the working directory to where all the model
    # files are located, then run twoarray.
    # Change back when done.
    prevdir = os.getcwd()
    cd(results_dir)
    
    
    # Setup the full PATH to the executable
    exe = os.path.join(code_dir,'twoarray.exe')
    
    errlist = mydef.ErrorListValues()
    
    try:
        # Define the executable process
        # The [] contains: [executable, option_arg_1, option_arg_2, etc.]
        p = subprocess.Popen([exe,file_in],
                             stdout = subprocess.PIPE,
                             stdin = subprocess.PIPE,
                             stderr = subprocess.PIPE)
        
        
        # Execute the code with any command-line arguments
        # Syntax: p.communicate(stdin)
        # Returns a tuple (stdoutdata, stderrdata)
        standardout, standarderror = p.communicate()
        
        # Raise an exception if an error occurs
        #   - Check for error keywords
        #   - Check the subprocess returncode
        #   - Check if any output was given to stderr
        error_flag = False
        for erritem in errlist.ErrorList:
            stdoutindex = standardout.find(erritem)
            stderrindex = standardout.find(erritem)
            #print ('Stdoutindex {}; Stderrindex {}\n'.format(stdoutindex,stderrindex))
            if (stdoutindex != -1 or stderrindex != -1):
                error_flag=True
                break
            # END if
        # END for over erritem
        if (p.returncode != 0 or standarderror or error_flag):
            currentmessage= ('ERROR:\t' +
                             'There was a problem running the ' +
                             'PEST utility twoarray!\n' +
                             '\tBelow is the report:\n' +
                             'Error code: {}\n'.format(p.returncode) +
                             'Standard Out:\n{}\n'.format(standardout))
            with open(logfile,'a') as lf: lf.write(currentmessage)
            error_message = standarderror
            raise ValueError(error_message)
    except ValueError as VError:
        #raise
        with open(logfile,'a') as lf: lf.write('{}'.format(VError))
        return False
    else: # All went well. Write the output to the logfiles and move on
        with open(twoarraylog,'w') as fout:
            fout.write('{}\n'.format(standardout))
        #
        with open(logfile,'a') as lf: lf.write('{}\n'.format(standardout))
    # END try
    
    cd(prevdir)
    
    return True

# ooooooooooooooooooooooooooooooooooooooooooooooooooooo

