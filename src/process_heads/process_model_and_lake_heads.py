# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 16:14:55 2020

@author: pbremner
"""

#==============================================================================
# Run program to extract model-wide heads and area-averaged lake heads.
# Process results to create model-wide dH files that are compatible with
# existing mapping scripts.
#
# Must use Python2.7 compliant python for now to work with ArcMap 10.6
#
# Written 20201223. PMBremner
#
# TODO
# - At later time, update the mapping script to use the single output
#   dH file (maybe transformed to csv?), and then update this script
#   to accommodate
#==============================================================================


#import sys
import os
import numpy as np
import subprocess
# Import internal python scripts
#src_dir = os.path.join(os.getcwd(),'../..')
#sys.path.insert(0,src_dir)
from utilities import mydefinitions as mydef
from utilities import basic_utilities as bscut



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Calculate the model-wide change in heads
# for each layer, and the area-weighted
# change in heads beneath lakes.
#
# Function uses Fortran code to extract heads
# from the binary MODFLOW heads file.
#
# Inputs:
#    - an input-control-file specifying input and
#      outputs for the Fortran routine
#    - the heads file(s) to be processed
#    - the lake definitions file(s) that list lake
#      area per model cell
#
# Outputs:
#    - model-wide dH for every model layer
#    - area-weighted averaged heads beneath lakes
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

def calc_dh (code_dir, input_countrol_file, runmode, logfile):
    
    program = os.path.join(code_dir,'nfseg_extract_modelwide_and_lake_hds.exe')
    #input_countrol_file = 'hds_processing_control_file.txt'
    
    
    errlist = mydef.ErrorListValues()
    
    try:
        # Define the executable process
        # The [] contains: [executable, option_arg_1, option_arg_2, etc.]
        # p = subprocess.Popen([exe,argument_list],
        #                      stdout = subprocess.PIPE,
        #                      stdin = subprocess.PIPE,
        #                      stderr = subprocess.PIPE)
        p = subprocess.Popen([program,'-in',input_countrol_file,'-runmode',runmode],
                             stdout = subprocess.PIPE,
                             stdin = subprocess.PIPE,
                             stderr = subprocess.PIPE)
        
        # Execute the code with any command-line arguments
        # Syntax:
        #       p.communicate(stdin) -- if stdin is needed
        #       p.communicate() -- if no stdin is needed
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
                             'There was a problem running {}!\n' +
                             '\tBelow is the report:\n' +
                             'Error code: {}\n'.format(program,p.returncode) +
                             'Standard Out:\n{}\n'.format(standardout))
            print(currentmessage)
            with open(logfile,'a') as lf: lf.write(currentmessage)
            error_message = standarderror
            raise ValueError(error_message)
    except ValueError as VError:
        #raise
        with open(logfile,'a') as lf: lf.write('{}'.format(VError))
        raise ValueError(VError)
        
    else: # All went well. Print output and move on
        if (runmode == 'run'):
            with open(logfile,'a') as lf: lf.write('{}\n'.format(standardout))
            return
        elif (runmode == 'readonly'):
            return standardout
    # END try
# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Read and parse input-control file used for calc_dh.
# Collect and return the output filenames
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
def get_input_output_fnames(code_dir, input_countrol_file, runmode, modlayers, logfile):
    
    # Create list of output files from processing heads
    #---------------------------------------------------
    output = calc_dh(code_dir, input_countrol_file, runmode, logfile)
    
    # Parse the output of reading the input-control-file
    WBfiles_in = {}
    WBfiles_out = {}
    WBfiles_initialized = False # flag to notify when file labels are setup
    for line in output.split('\n'):
        line = line.split()
        if (len(line)>0):
            if (line[:2] == ['dH','filename(s):']):
                dHfile = line[2]
                #print(line[2])
            elif (line[:9] == ['Number',
                               'of',
                               'Waterbody',
                               '(WB)',
                               'input',
                               'files',
                               'and',
                               'output',
                               'prefixes:']):
                n_WB_files = np.int(line[9])
                #print(n_WB_files)
                
                for i in range(n_WB_files):
                    label = 'WB_{}'.format(i+1)
                    WBfiles_in.update({label:''})
                    WBfiles_out.update({label:[]})
                WBfiles_initialized = True
            else:
                if WBfiles_initialized:
                    #print(line[2])
                    
                    # Retrieve the lake input filename.
                    # Construct the WaterBody output filenames from
                    # the file prefix and each model layer number
                    # for the current key
                    if line[0] in WBfiles_in:
                        WBfiles_in[line[0]] = '{}'.format(line[1])
                        for lay in modlayers:
                            WBfiles_out[line[0]].append('{}_layer_{}.txt'.format(line[2],lay))
                        #
#                   #
                #
            #
        #
    #
    
    return dHfile,WBfiles_in,WBfiles_out
# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
# Reformat space delimited dh data for each model
# layer as csv.
#
# Output new csv files for each model layer.
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
def reformat_dh_modlayers_space2csv(dHfile, uselayers):
    
    # Setup a dictionary to define which columns to convert.
    # At the same time, setup a dictionary to define the output filenames.
    sequencenum = 'SeqNum'
    relevantcol = {sequencenum:0} # sequence number is always used
    outfiles = {} # dictionary for output filenames
    outf = {} # dictionary for the file objects
    outheader = {} # dictionary for the header line of each output file
    outfiles_n_labels = {} # dictionary of the outfile names and the associated table labels
    for lay in uselayers:
        label = 'Layer{}'.format(lay)
        tablelabel = 'dh_lyr{}'.format(lay)
        fieldlabel = 'dh_layer{}'.format(lay)
        relevantcol.update({label:0})
        outfile = 'dh_{}_tableFormat.csv'.format(label)
        outfiles.update({label:outfile})
        outf.update({label:'fout{}'.format(lay)})
        #outheader.update({label:'cellAddress2D,dh_lyr{}\n'.format(lay)})
        outheader.update({label:'cellAddress2D,dh_lyr{}\n'.format(lay)})
        outfiles_n_labels.update({label:[outfile,tablelabel,fieldlabel]})
    #
    
    # Read in the data, starting with the header to locate column positions
    with open(dHfile, 'r') as fin:
        # Read the first header line to see where things are
        headerin = fin.readline().rstrip().split()
        
        # Find the relevant columns -- record the column position
        for i,col in enumerate(headerin):
            if (col in relevantcol): relevantcol[col] = i
        #
        
        # Open all the output files and read all the
        # data lines (as strings) for the relevant columns
        # Write the data directly to the output files
        for key,value in outfiles.items():
            outf[key] = open (value,'w')
            
            # Write the header line
            outf[key].write (outheader[key])
        #
        
        # Read the remaining data lines and put data in proper places as csv
        for line in fin:
            
            # Split the data just once
            dcolumns = line.rstrip().split()
            
            # Parse the data line
            for colkey in relevantcol.keys():
                if (colkey!=sequencenum):
                    outf[colkey].write ('{},{}\n'.format(dcolumns[relevantcol[sequencenum]],
                                                         dcolumns[relevantcol[colkey]]))
                #
            #
        #
    #  End with
    
    # Close all the output files
    for key,fobj in outf.items(): fobj.close()
    
    return outfiles_n_labels
# ooooooooooooooooooooooooooooooooooooooooooooooooooooo



#==============================================================================
#
# MAIN PROGRAM
#
#==============================================================================

def main(input_countrol_file, modlayers, uselayers, code_dir, postproc_deffiles_lakef, results_postproc_dh, logfile):
    
    # Change the working directory to where heads processing takes place.
    # Change back when done.
    prevdir = os.getcwd()
    bscut.cd(results_postproc_dh)
    
    # Just read the input-control file. The output
    # from reading this file provides the program
    # output filenames needed to reformat the
    # output to work with existing scripts that
    # add data to geodatabases.
    #---------------------------------------------------
    runmode = 'readonly'
    dHfile,WBfiles_in,WBfiles_out = get_input_output_fnames(code_dir, input_countrol_file, runmode, modlayers, logfile)
    
    #print (dHfile,WBfiles_out)
    
    
    # Copy the relevant lake files to the working directory
    for keys,lakef in WBfiles_in.items():
        if not (bscut.copyfile(os.path.join(postproc_deffiles_lakef,lakef)
                           ,lakef
                           ,logfile)): continue
    
    # Run the program again, but this time process model heads
    #     -- model-wide dH and heads beneath lakes
    runmode = 'run'
    calc_dh(code_dir, input_countrol_file, runmode, logfile)
    
    
    # Reformat the dH file to csv for import into gdb
    # NOTE: For now this makes separate layer files to immediately
    #       work with the existing script to map the results.
    #       Later that mapping script should process multiple
    #       columns of data at once.
    # TODO: Change the formatting to produce a single
    #       csv file containing all model layers. This would
    #       be the equivalent of the calc_dh program output
    #       but converting as space-to-comma delimited.
    #---------------------------------------------------
    outfiles_list = reformat_dh_modlayers_space2csv(dHfile, uselayers)
    
    
    currentmessage = ('\n\t. . . Done processing heads!\n\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    # Done here -- move back to the main working directory
    bscut.cd(prevdir)
    
    return outfiles_list
#==============================================================================
#==============================================================================
#exit()