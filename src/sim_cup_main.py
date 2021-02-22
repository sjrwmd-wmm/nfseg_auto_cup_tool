#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
# The main script to process the NFSEG WUP Tool
#
# WARNING:  This tool uses python libraries from ArcGIS - arcpy
#           arcpy from version ArcGIS 10.6 or newer is required
#
# Written 20200318. PMBremner
#
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
# IMPORT ALL LIBRARIES AND SETUP BASIC GLOBAL PATHs
#
#xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxo

#import sys
# switch to pathlib library for Python3 where appropriate
import errno
import os
import ntpath
import zipfile
#import numpy
#from copy import deepcopy as dc
#import itertools
import shutil

# ---------------   Set some immediate working directories
# Get the current working directory
cur_working_dir = '/'.join(os.getcwd().split('\\'))
#cur_working_dir = os.path.join(*os.getcwd().split('\\')) # the * unpacks the list

# Define the results parent directory
results_main_dir = os.path.abspath(os.path.join(cur_working_dir,os.pardir))
#results_main_dir = os.path.join(*os.path.split(cur_working_dir)[:-1])

# Find way to src directory  !!! PMB !!! Remove these lines when ready
src_dir = os.path.join(cur_working_dir,'src')
#src_utilities_dir = os.path.join(src_dir,'utilities')
#src_preprocess_dir = os.path.join(src_dir,'preprocess')
src_postprocess_dir = os.path.join(src_dir,'postprocess')

# Insert the PATH to internal python scripts
##sys.path.insert(0,src_utilities_dir)
##sys.path.insert(0,src_preprocess_dir)
##sys.path.insert(0,src_postprocess_dir)
##print(sys.path)

# ---------------   Import utilities
from utilities import basic_utilities as bscut
from utilities import mydefinitions as mydef

# ---------------   Import preprocess
from preprocess import process_withdrawal_point_input_file
from preprocess import update_wellpkg_nfseg_v3 as update_wellpkg_nfseg
from preprocess import create_two_stress_period_wellpkg_input_file

# ---------------   Import postprocess
from postprocess import parse_modflow_listing_file_budget
from postprocess import river_drain_and_ghb_flux_changes
from postprocess import sim_q_reach_3d_auto
from postprocess import sum_sim_q_reach
from postprocess import create_delta_q_report_PMB
#from postprocess import ReadModflowFloatArrays
from postprocess import make_ArcGIS_table_from_csv

# ---------------   Import process_heads
from process_heads import process_model_and_lake_heads

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
# MAIN PROGRAM
#
#xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxo

# Print the banner
mydef.introbanner()


usermessage_1 = 'Please supply an input csv file name: '
usermessage_rest = 'More? Please supply another input csv file name (input "exit" if done): '

loopcount = 0
continueloop = True

exit_message = ['exit','EXIT','Exit']

while continueloop:
    
    # Increment the tracker
    loopcount = loopcount + 1
    
    # ---------------------------------------
    # Receive user input from the command-line
    #     ARG_1 = USER_SUPPLIED_INPUT_FILE
    #     ARG_2 = SRWMD or SJRWMD
    # * SRWMD or SJRWMD use different map projections.
    # * The User should select the option that matches
    # * the map projection used when obtaining
    # * the X,Y coordinats of the potential wells.
    #
    # NOTE: PROGRAM WILL EXIT WHEN USER
    #       SPECIFIES AN exit_message
    # ---------------------------------------
    # SET INPUT_FILE=sim_cup_input_DD_MSDOS.csv
    # SET INPUT_FILE="sim_cup_input_DD.csv"
    
    if (loopcount==1): INPUT_FILE = raw_input(usermessage_1)
    elif (loopcount>1):
        INPUT_FILE = raw_input(usermessage_rest)
    #
    
    # Set continueloop = False if an exit message was input
    for iexit in exit_message:
        if (INPUT_FILE==iexit):
            continueloop = False
            break
        # END if
    # END for over item
    
    # Check if we need to break out of the while loop
    if not continueloop: break
    
    
    # =====================================================
    # Parse input file to construct output report filenames
    # Define the log file name
    # =====================================================
    # Remove the extension from the filename and capture the basename
    # A '.' is put back in for all other (non-suffix) components that are split
    # The base filename gets extracted from the path if the input file
    #     is in its own directory
    basename = '.'.join(ntpath.basename(INPUT_FILE).split('.')[:-1])
    #
    # Name the resuls directory
    results_dirname = (basename + '_results')
    results_dirname = os.path.join(results_main_dir,results_dirname)
    
    # Ask before creating a new results directory
    usermessage_2 = '\nPrexisting results with the jobname {} will be overwritten. Proceed? ( Y = yes , N = no )\n'.format(results_dirname)
    OVERWRITE = 'Y'
    OVERWRITE = raw_input(usermessage_2)
    if (OVERWRITE=='N' or OVERWRITE=='n' or OVERWRITE=='no' or OVERWRITE=='NO' or OVERWRITE=='No'):
        # Give the user a message and move to a new iteration
        print ('\n\nSkipping this job and moving to the next...\n\n')
        continue
    elif (OVERWRITE=='Y' or OVERWRITE=='y' or OVERWRITE=='yes' or OVERWRITE=='YES' or OVERWRITE=='Yes'):
        print ('\n\nCreating or replacing {}\n\n'.format(results_dirname))
        if os.path.isdir(results_dirname):
            # The directory already exists -- replace it
            shutil.rmtree(results_dirname,ignore_errors=True)
            try:
                # Sometimes the deletion takes too long and throws an error
                # when making a new directory...
                # This try statement slows it down to finish removing
                # the directory before trying again to make it.
                os.mkdir(results_dirname)
            except WindowsError as wexc: # !!! May need to correct this PMB
                #WindowsError: [Error 183] Cannot create a file when that file already exists:
                # Try deleting again
                shutil.rmtree(results_dirname,ignore_errors=True)
                os.mkdir(results_dirname)
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
                else:
                    # Try deleting again
                    shutil.rmtree(results_dirname,ignore_errors=True)
                    os.mkdir(results_dirname)
                #
            #
        elif not os.path.isdir(results_dirname):
            # The directory doesn't exist, make it now
            os.mkdir(results_dirname)
        #
    else:
        print ('\n\nOption not recognized, please try again...\n\n')
    #
    
    # Name the logfile that will capture all events
    # Replace existing logfile or start a new one
    logfile = (os.path.join(results_dirname, (basename+'.log') ) )
    if os.path.isfile(logfile): os.remove(logfile)
    # -----------------------------------------------------
    
    
    # Start log file with the banner
    with open(logfile,'a') as lf: lf.write('{}\n'.format(mydef.logbanner()))
    
    
    # Check that the User-Input filename exists
    # Print the ERROR and Move to the next loop iteration
    # if there is a problem
    try:
        mydef.checkfileexist(INPUT_FILE)
    except ValueError as VError:
        #raise
        print ('\n{}'.format(VError))
        with open(logfile,'a') as lf: lf.write('\n{}'.format(VError))
        continue # Continue to next iteration
    else:
        pass
    # end try

    PROJECTION = raw_input('\nPlease input the map projection type used - in all caps - or the associated number\n' +
                        '(options are 1=SRWMD or 2=SJRWMD. Different names result in a poetic exit): ')
    # PROJECTION = raw_input("Please input the map projection type used in all caps (options are SRWMD or SJRWMD. Different names result in a poetic exit): ")
    # PROJECTION = 'SRWMD'

    ALLOWED_PROJ = ['SRWMD','SJRWMD','1','2']

    # Check that the user supplied an acceptable PROJECTION
    try:
        mydef.projcheck(PROJECTION,ALLOWED_PROJ)
    except ValueError as VError:
        #raise
        print ('\n{}'.format(VError))
        with open(logfile,'a') as lf: lf.write('\n{}'.format(VError))
        continue # Continue to next iteration
    else:
        # Incase of numeral input, reset the PROJECTION to appropriate district name
        if (PROJECTION == '1'): PROJECTION = 'SRWMD'
        elif (PROJECTION == '2'): PROJECTION = 'SJRWMD'
        
        currentmessage = ('\nUser supplied input file:  ' + INPUT_FILE +
                          '\nProjection type:  ' + PROJECTION + '\n\n')
        print (currentmessage)
        with open(logfile,'a') as lf: lf.write(currentmessage)
    # end if

    # Set the map projection based on the user option
    if (PROJECTION == 'SRWMD'):
        mapproj = 'state_plane_north'
    elif (PROJECTION == 'SJRWMD'):
        mapproj = 'utm_zone17N_linear_unit_meters_sjr'
    # END if
    # =======================================
    
    
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #
    # SETUP THE NEW RESULTS DIRECTORY AND ASSIGN PATHs
    #
    #xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxo
    
    # Copy the input file to the results directory
    currentmessage = ('\n\nCopy the User input file:\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    if not (bscut.copyfile(INPUT_FILE, os.path.join(results_dirname,ntpath.basename(INPUT_FILE)), logfile)): continue
    
    
    # =====================================================
    # Define the working and results directories
    # =====================================================
    
    # GIS directory
    # TODO: Get the gis name capitalized
    gis_dir = os.path.join(cur_working_dir,'gis')

    # Model files directory
    model_dir = os.path.join(cur_working_dir,'model_update')

    # MODFLOW executable directory
    mfexe_dir = os.path.join(cur_working_dir,'model_update')
    
    # Process heads executable directory
    phexe_dir = os.path.join(cur_working_dir,'src','process_heads')
    
    # Preprocessing working directory
    preproc_cwd = os.path.join(cur_working_dir,'preproc','wellpkg_update')
    #preproc_cwd = os.path.join(cur_working_dir,'results')
    
    # Postprocessing budget directory
    postproc_dh_cwd = os.path.join(cur_working_dir,'postproc','dh')

    # Postprocessing budget directory
    postproc_dQ_cwd = os.path.join(cur_working_dir,'postproc','dQ')
    
    
    # -----------------------------------
    # Define the location of input and
    # definition files and gis reference
    # files and folders
    # -----------------------------------
    input_def_file_loc = os.path.join(cur_working_dir,'input_and_definition_files')
    
    preproc_deffiles_dir = os.path.join(input_def_file_loc,'preproc')
    #
    preproc_deffiles_wellpkg_update = os.path.join(preproc_deffiles_dir,'wellpkg_update.zip')
    
    postproc_deffiles_dir = os.path.join(input_def_file_loc,'postproc')
    #
    postproc_deffiles_budget = os.path.join(postproc_deffiles_dir,'budget')
    postproc_deffiles_dh = os.path.join(postproc_deffiles_dir,'dh')
    postproc_deffiles_dQ = os.path.join(postproc_deffiles_dir,'dQ')
    postproc_deffiles_lakehds = os.path.join(postproc_deffiles_dir,'nfseg_avg_lake_hds')
    postproc_deffiles_lakef = os.path.join(postproc_deffiles_lakehds,'lake_files')
    
    # The GIS reference files and folders
    gis_ref_cupgdb = os.path.join(gis_dir,'cup.gdb.zip')
    gis_ref_mxd = 'dh.mxd'  # located in gis_dir
    gis_ref_projections = os.path.join(gis_dir,'projections')
    
    
    # -----------------------------------
    # Define the results directories
    # -----------------------------------
    
    # Preprocessing directory
    results_preproc = os.path.join(results_dirname,'preproc')
    
    # Wellpkg_update directory
    results_preproc_wellpkg_update = os.path.join(results_dirname,'preproc','wellpkg_update')
    
    # Postprocessing directory
    results_postproc = os.path.join(results_dirname,'postproc')
    
    # Postprocessing budget directory
    results_postproc_budget = os.path.join(results_postproc,'budget')
    
    # Postprocessing budget directory
    results_postproc_dh = os.path.join(results_postproc,'dh')
    
    # Postprocessing budget directory
    results_postproc_dQ = os.path.join(results_postproc,'dQ')
    
    # GIS directory in the results directory
    results_gis = os.path.join(results_dirname,'gis')
    results_gisproj = os.path.join(results_gis,'projections')
    # -----------------------------------
    
    
    # =====================================================
    #
    # Setup the results directory and copy the
    # necessary files over
    #
    # =====================================================
    
    # -------------------
    #       Preproc
    # -------------------
    os.mkdir(results_preproc)
    
    #os.mkdir(results_preproc_wellpkg_update)
    with zipfile.ZipFile(preproc_deffiles_wellpkg_update,'r') as zip_ref:
        zip_ref.extractall(results_preproc)
    #
    
    # --------------------
    #       Postproc
    # --------------------
    os.mkdir(results_postproc)
    
    # Budget
    os.mkdir(results_postproc_budget)
    
    # dH
    os.mkdir(results_postproc_dh)
    # Copy the input control file
    input_countrol_file = 'hds_processing_control_file.txt'
    input_countrol_file_n_path = os.path.join(results_postproc_dh,input_countrol_file)
    if not (bscut.copyfile(os.path.join(postproc_deffiles_dh,input_countrol_file),
                           input_countrol_file_n_path,
                           logfile)): continue
    
    # dQ
    os.mkdir(results_postproc_dQ)
    if not (bscut.copyfile(os.path.join(postproc_deffiles_dQ,'gaged_reach_definitions.csv'),
                           os.path.join(results_postproc_dQ,'gaged_reach_definitions.csv'),
                           logfile)): continue
    # The shelf file can be referenced from the deffiles location -- no need to copy
    #if not (bscut.copyfile(os.path.join(postproc_deffiles_dQ,'lookup_bc_reach_ids_auto.shelf'),
    #                       os.path.join(results_postproc_dQ,'lookup_bc_reach_ids_auto.shelf'),
    #                       logfile)): continue
    if not (bscut.copyfile(os.path.join(postproc_deffiles_dQ,'station_number_and_names_20210218.csv'),
                           os.path.join(results_postproc_dQ,'station_number_and_names_20210218.csv'),
                           logfile)): continue
    if not (bscut.copyfile(os.path.join(postproc_deffiles_dQ,'upstream_gage_numbers.csv'),
                           os.path.join(results_postproc_dQ,'upstream_gage_numbers.csv'),
                           logfile)): continue
    
    
    # ---------------
    #      GIS
    #----------------
    os.mkdir(results_gis)
    
    with zipfile.ZipFile(gis_ref_cupgdb,'r') as zip_ref:
        zip_ref.extractall(results_gis)
    #
    
    # Copy template dh.mxd to results directory
    if not (bscut.copyfile(os.path.join(gis_dir,gis_ref_mxd),
                           os.path.join(results_gis,gis_ref_mxd),
                           logfile)): continue
    
    os.mkdir(results_gisproj)
    # Define the name for a new set of grid feature classes
    # TODO: this name either needs to be generic or be part of input file
    #grid_featureclass_name = os.path.join(results_postproc_dh,'nfseg_v1_1_grid')
    grid_featureclass_name = 'nfseg_v1_1_grid'
    grid_featureclass_proj = os.path.join(results_gisproj,(grid_featureclass_name+'.prj'))
    mapprojection = os.path.join(results_gisproj,(mapproj+'.prj'))
    #
    # Copy relevant projection files to the new results directory
    if not (bscut.copyfile(os.path.join(gis_ref_projections,(mapproj+'.prj')),
                           mapprojection,
                           logfile)): continue
    if not (bscut.copyfile(os.path.join(gis_ref_projections,(grid_featureclass_name+'.prj')),
                           grid_featureclass_proj,
                           logfile)): continue
    
    # _____________________________________________________
    # -----------------------------------------------------
    
    
    # =====================================================
    #
    # Setup the results filenames.
    # Change the names of the reports to carry
    # the basename of the input file.
    #
    # =====================================================
    
    # Setup a suffix that will be appended to the basename
    suffix_DQ = 'delta_q_summary'
    suffix_budget = 'global_budget_change'

    # Append the suffix and extension to the basename
    DQ_summary_out_fname = (basename + '_' + suffix_DQ + '.csv')
    DQ_summary_out = os.path.join(results_dirname,DQ_summary_out_fname)
    D_global_budget_out_fname = (basename + '_' + suffix_budget + '.csv')
    D_global_budget_out = os.path.join(results_dirname,D_global_budget_out_fname)
    currentmessage = ('\n\nResults directory location and name:\n\t' +
                      results_dirname + '\n\n'
                      'CSV filenames output to results directory:\n\t' +
                      DQ_summary_out_fname + '\n\t' +
                      D_global_budget_out_fname + '\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    # Delete previous versions of the output files, if they exist
    # These will be recreated
    bscut.deletefile(DQ_summary_out,logfile)
    bscut.deletefile(D_global_budget_out,logfile)
    # -----------------------------------------------------
    
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #
    # PREPROCESS
    #
    #xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxo
    
    # =====================================================
    # Process the input csv file
    # =====================================================

    currentmessage = ('\n\nCreating wellpkg with cup withdrawals . . .\n\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)


    # Define the wel file since it's used multiple times
    wel_file = os.path.join(results_preproc_wellpkg_update,'nfseg_auto.wel')

    # Delete files that will be created again, if they exist
    bscut.deletefile(wel_file,logfile)
    bscut.deletefile(os.path.join(results_preproc_wellpkg_update,'wells_to_add.txt.xml'),logfile)
    bscut.deletefile(os.path.join(results_preproc_wellpkg_update,'wells_to_add.csv'),logfile)
    bscut.deletefile(os.path.join(results_preproc_wellpkg_update,'withdrawal_point_locations_and_rates.csv'),logfile)


    currentmessage = ('\nStarting process_withdrawal_point_input_file.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    process_withdrawal_point_input_file.main(INPUT_FILE,results_preproc_wellpkg_update,
                                             mydef.ConvFactors().mgd2cfd,logfile)

    currentmessage = ('\nStarting update_wellpkg_nfseg_modified.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    # Argument provides the correct map projection
    update_wellpkg_nfseg.main(mapprojection, results_preproc_wellpkg_update,
                              results_gis, grid_featureclass_name, grid_featureclass_proj,
                              logfile)



    currentmessage = ('\nStarting create_two_stress_period_wellpkg_input_file.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    create_two_stress_period_wellpkg_input_file.main(wel_file,results_preproc_wellpkg_update,logfile)

    #    Finished creating well pkg.

    # Print out the date and time of processing
    print (bscut.datetime())
    with open(logfile,'a') as lf: lf.write('{}'.format(bscut.datetime()))
    # -----------------------------------------------------


    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #
    # SETUP AND RUN MODFLOW
    #
    #xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxo

    currentmessage = ('\n\nExecuting model . . .\n' +
                      '\t--- first delete old files (if they exist) ---\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)

    # Delete files that will be created again, if they exist
    bscut.deletefile(os.path.join(model_dir,'nfseg_auto.lst'),logfile)
    bscut.deletefile(os.path.join(model_dir,'nfseg_auto.cbb'),logfile)
    bscut.deletefile(os.path.join(model_dir,'nfseg_auto.cbw'),logfile)
    bscut.deletefile(os.path.join(model_dir,'nfseg_auto.crc'),logfile)
    bscut.deletefile(os.path.join(model_dir,'nfseg_auto.hds'),logfile)
    bscut.deletefile(os.path.join(model_dir,'nfseg_auto.ddn'),logfile)
    bscut.deletefile(os.path.join(model_dir,'nfseg_auto.wel'),logfile)

    # Copy the new wel file to the model directory
    # TODO: Change for modflow to somehow use the same file as what is output in previous step -- no duplication.
    #       move instead of copy?
    if not (bscut.copyfile(wel_file, os.path.join(model_dir,'nfseg_auto.wel'), logfile)): continue

    currentmessage = ('\nExecuting modflow. This may take a few moments . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)

    nam_file = os.path.join(model_dir,'nfseg_auto_2009.nam')
    
    if not bscut.modflow(mfexe_dir,model_dir,nam_file,logfile): continue
    
    # -----------------------------------------------------
    
    
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #
    # POSTPROCESS
    #
    #xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxo
    
    # Copy MODFLOW results to postprocessing directories
    if not (bscut.copyfile(os.path.join(model_dir,'nfseg_auto.lst')
                           ,os.path.join(results_postproc_dQ,'nfseg_auto.lst')
                           ,logfile)): continue
    
    if not (bscut.copyfile(os.path.join(model_dir,'nfseg_auto.hds')
                           ,os.path.join(results_postproc_dh,'nfseg_auto.hds')
                           ,logfile)): continue
    
    # Define a name for the list file output from MODFLOW after it is copied
    # to the results directory
    listfile = os.path.join(results_postproc_budget,'nfseg_auto.lst')
    
    # The results directory
    if not (bscut.copyfile(os.path.join(model_dir,'nfseg_auto.lst')
                           ,listfile
                           ,logfile)): continue
    
    # ---------------------------------------
    # Generate the budget check reports
    # ---------------------------------------

    currentmessage = ('\n\nGenerate budget check reports . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    # Name output files that will be recreated
    budoutput = D_global_budget_out
    rivfluxoutput = os.path.join(results_postproc_budget,'global_river_plus_drain_flux_changes.asc')
    
    
    # Delete files that will be created again, if they exist
    bscut.deletefile(budoutput,logfile)
    bscut.deletefile(rivfluxoutput,logfile)
    
    
    currentmessage = ('\nStarting parse_modflow_listing_file_budget.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    parse_modflow_listing_file_budget.main(listfile, budoutput, logfile)
    
    currentmessage = ('\nStarting river_drain_and_ghb_flux_changes.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    river_drain_and_ghb_flux_changes.main(budoutput, rivfluxoutput, logfile)
    
    # =======================================
    
    
    # ---------------------------------------
    # Generate the change in flow reports
    # ---------------------------------------

    currentmessage = ('\n\ngenerate simulated river and spring flux change reports . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)

    # Define some intermediate output filenames
    temp_shelf = os.path.join(results_postproc_dQ,'temp.shelf')
    cup_id_n_rate = os.path.join(results_postproc_dQ,'cup_id_and_rate.csv')
    
    # Delete files that will be created again, if they exist
    bscut.deletefile(temp_shelf,logfile)
    bscut.deletefile(cup_id_n_rate,logfile)
    
    if not (bscut.copyfile(os.path.join(results_preproc_wellpkg_update,'cup_id_and_rate.csv')
                           , cup_id_n_rate
                           , logfile)): continue
    
    currentmessage = ('\nStarting sim_q_reach_3d_auto.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    gaged_reach_flux_out = os.path.join(results_postproc_dQ,'gaged_reach_fluxes.asc')
    
    sim_q_reach_3d_auto.main(listfile,
                             mydef.ConvFactors().sec2day,
                             logfile,
                             postproc_deffiles_dQ,
                             results_postproc_dQ,
                             gaged_reach_flux_out)
    
    currentmessage = ('\nStarting sum_sim_q_reach.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    gaged_flux_sum_output = os.path.join(results_postproc_dQ,'gaged_fluxes_sum.csv')
#    sum_sim_q_reach.main(logfile,
#                         postproc_deffiles_dQ,
#                         gaged_reach_flux_out,
#                         gaged_flux_sum_output)
    sum_sim_q_reach.main(logfile,
                         results_postproc_dQ,
                         gaged_reach_flux_out,
                         gaged_flux_sum_output)
    

    currentmessage = ('\nStarting create_delta_q_report.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
#    create_delta_q_report.main(logfile,
#                               postproc_deffiles_dQ,
#                               cup_id_n_rate,
#                               gaged_reach_flux_out,
#                               gaged_flux_sum_output,
#                               DQ_summary_out)
    create_delta_q_report_PMB.main(logfile,
                               results_postproc_dQ,
                               cup_id_n_rate,
                               gaged_reach_flux_out,
                               gaged_flux_sum_output,
                               DQ_summary_out)
    # =======================================


    # ---------------------------------------
    # Process model-wide and area-averaged
    # lake heads and change in heads
    # ---------------------------------------
    
    currentmessage = ('\n\nProcessing model-wide and area-averaged lake heads . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    all_model_layers = [1,2,3,4,5,6,7]
    model_layers_to_use = [1,3,5]
    
    dh_layer_dictionary = process_model_and_lake_heads.main(input_countrol_file_n_path,
                                                            all_model_layers,
                                                            model_layers_to_use,
                                                            phexe_dir,
                                                            postproc_deffiles_lakef,
                                                            results_postproc_dh,
                                                            logfile)
    # =======================================
    
    
    # ---------------------------------------
    # Update and finalize the map project in GIS dir
    #
    # Add dH results to a geodatabase using the ArcPy
    # utilities. The geodatabase is viewable in ArcMap.
    #
    # IMPORTANT:
    # The function currently uses the (now deprecated)
    # Python2.7 that is bundled with ArcMap 10.X.
    # Later versions that either upgrade to ArcPro
    # or use GDAL libraries will need upgrade to
    # Python3.X.
    #
    # Inputs:
    #    - the current-working directory that contains
    #      the dH files
    #    - the gis directory that contains the gdb
    #    - the list of files to process data from
    # TODO: - add the lake definitions file(s) that list lake
    #      area per model cell
    #
    # Outputs:
    #    - updated gdb
    #
    # ---------------------------------------
    currentmessage = ('\n\nGenerate simulated head change maps . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    make_ArcGIS_table_from_csv.main(dh_layer_dictionary,
                                    results_postproc_dh,
                                    results_gis,
                                    grid_featureclass_name,
                                    logfile)


    currentmessage = ('\n\tMaps generated\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    # =======================================
    
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #
    # FINALIZE CURRENT RUN
    #
    #xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxo


    # =====================================================
    # Finalize the current Process Iteration
    # =====================================================
    
    currentmessage = ('\n\nResults directory location and name:\n\t' +
                      results_dirname + '\n\n'
                      'CSV filenames output to results directory:\n\t' +
                      DQ_summary_out_fname + '\n\t' +
                      D_global_budget_out_fname + '\n\n' +
                      'Log output written to:\n\t' +
                      logfile)
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    currentmessage = ('\n\n\n' +
                      '\t\txoxoxoxoxoxoxoxoxoxoxoxox\n\n' +
                      '\t\t-- PROCESSING COMPLETE --\n\n' +
                      '\t\txoxoxoxoxoxoxoxoxoxoxoxox\n\n\n' +
                      'If no Error or Warning messages appeared ' +
                      'then the simulation was successful!\n\n\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    # -----------------------------------------------------
    
# END while over continueloop
#pause ()
#exit()
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
# END SCRIPT
#
#xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxo
