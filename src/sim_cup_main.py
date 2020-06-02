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

import sys
import os
import numpy
from copy import deepcopy as dc
import itertools
import shutil

# Import tool libraries
# ================================
# Find way to src directory
src_dir = '/'.join(os.getcwd().split('\\'))
src_dir = os.path.join(src_dir,'src')
# Insert the PATH to internal python scripts
src_utilities_dir = os.path.join(src_dir,'utilities')
src_preprocess_dir = os.path.join(src_dir,'preprocess')
src_postprocess_dir = os.path.join(src_dir,'postprocess')
sys.path.insert(0,src_utilities_dir)
sys.path.insert(0,src_preprocess_dir)
sys.path.insert(0,src_postprocess_dir)
import basic_utilities as bscut
import mydefinitions as mydef
#import text_blocks_and_errors as mytxterr
import process_withdrawal_point_input_file
import update_wellpkg_nfseg_modified
import create_two_stress_period_wellpkg_input_file
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
import parse_modflow_listing_file_budget
import river_drain_and_ghb_flux_changes
import sim_q_reach_3d_auto
import sum_sim_q_reach
import create_delta_q_report
import ReadModflowFloatArrays
import make_ArcGIS_table_from_csv
#=======================================
#many2one < many2one_layers1_and_3_hds_nfseg.inp > many2one.log
#twoarray < twoarray_dh_layer1_nfseg.inp > twoarray_dh_layer1.log
#twoarray < twoarray_dh_layer3_nfseg.inp > twoarray_dh_layer3.log
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# ================================

# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
#
#                      MAIN
#
# xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

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
    # TODO: Capture the results directory from this
    # TODO: Make this handle being in its own dir
    basename = '.'.join(INPUT_FILE.split('.')[:-1])
    #
    # Name the logfile that will capture all events
    logfile = (basename+'.log')
    # -----------------------------------------------------
    
    
    # Add the User INPUT_FILE name to the log file
    with open(logfile,'a') as lf: lf.write('{}\n'.format(INPUT_FILE))
    
    
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


    # Print out the date and time of processing
    print (bscut.datetime())
    with open(logfile,'a') as lf: lf.write('{}'.format(bscut.datetime()))
    
    
    # =====================================================
    # Define the working and results directories
    # =====================================================

    # Get the current working directory
    cur_working_dir = '/'.join(os.getcwd().split('\\'))

    # Define the GIS directory
    # TODO: Get the gis name capitalized
    gis_dir = os.path.join(cur_working_dir,'gis')

    # Define the model directory
    model_dir = os.path.join(cur_working_dir,'model_update')

    # Define the directory containing the MODFLOW executable
    mfexe_dir = os.path.join(cur_working_dir,'model_update')
    
    # Define the preprocessing working directory
    preproc_cwd = os.path.join(cur_working_dir,'preproc','wellpkg_update')
    
    # Define the postprocessing budget directory
    postproc_budget_cwd = os.path.join(cur_working_dir,'postproc','budget')

    # Define the postprocessing budget directory
    postproc_dh_cwd = os.path.join(cur_working_dir,'postproc','dh')

    # Define the postprocessing budget directory
    postproc_dQ_cwd = os.path.join(cur_working_dir,'postproc','dQ')
    
    
    # -----------------------------------
    # Define the location of input and
    # definition files
    # -----------------------------------
    input_def_file_loc = os.path.join(cur_working_dir,'input_and_definition_files')
    
    preproc_deffiles = os.path.join(input_def_file_loc,'preproc','wellpkg_update')
    
    postproc_deffiles_budget = os.path.join(input_def_file_loc,'postproc','budget')
    postproc_deffiles_dh = os.path.join(input_def_file_loc,'postproc','dh')
    postproc_deffiles_dQ = os.path.join(input_def_file_loc,'postproc','dQ')
    

    # -----------------------------------
    # Define the results directories
    # -----------------------------------
    # TODO: change this to be a different one for each job
    #       needs to be at the same time as the gis stuff
    # TODO: These results directories need to be created still !!! PMB
    #results_parent_dir = dc(cur_working_dir)
    results_parent_dir = os.path.join(cur_working_dir,'results')

    # Define the preprocessing directory
    preproc_results = results_parent_dir #os.path.join(results_parent_dir,'preproc','wellpkg_update')

    # Define the postprocessing budget directory
    postproc_budget_results = results_parent_dir #os.path.join(results_parent_dir,'postproc','budget')

    # Define the postprocessing budget directory
    postproc_dh_results = results_parent_dir #os.path.join(results_parent_dir,'postproc','dh')

    # Define the postprocessing budget directory
    postproc_dQ_results = results_parent_dir #os.path.join(results_parent_dir,'postproc','dQ')
    # -----------------------------------

    # Setup a suffix that will be appended to the basename
    suffix_DQ = 'delta_q_summary'
    suffix_budget = 'global_budget_change'

    # Append the suffix and extension to the basename
    DQ_summary_out = (basename + '_' + suffix_DQ + '.csv')
    DQ_summary_out = os.path.join(results_parent_dir,DQ_summary_out)
    D_global_budget_out = (basename + '_' + suffix_budget + '.csv')
    D_global_budget_out = os.path.join(results_parent_dir,D_global_budget_out)
    currentmessage = ('The output filenames will be:\n\t' + DQ_summary_out + '\n\t' + D_global_budget_out)
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    # -----------------------------------------------------


    # Delete previous versions of the output files, if they exist
    # These will be recreated
    bscut.deletefile(DQ_summary_out,logfile)
    bscut.deletefile(D_global_budget_out,logfile)


    # =====================================================
    # Process the input csv file
    # =====================================================

    currentmessage = ('\n\nCreating wellpkg with cup withdrawals . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)


    # Define the wel file since it's used multiple times
    wel_file = os.path.join(preproc_cwd,'nfseg_auto.wel')

    # Delete files that will be created again, if they exist
    bscut.deletefile(wel_file,logfile)
    bscut.deletefile(os.path.join(preproc_cwd,'wells_to_add.txt.xml'),logfile)
    bscut.deletefile(os.path.join(preproc_cwd,'wells_to_add.csv'),logfile)
    bscut.deletefile(os.path.join(preproc_cwd,'withdrawal_point_locations_and_rates.csv'),logfile)


    # TODO: delete these files when ready
    #bscut.deletefile(preproc_results + 'sim_cup_input.csv')) # Changing this to use original
    # Copy over the input file
    # copy ..\..\sim_cup_input_DD_MSDOS.csv sim_cup_input.csv
    #copy ..\..\%INPUT_FILE% sim_cup_input.csv
    currentmessage = ('\nStarting process_withdrawal_point_input_file.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    process_withdrawal_point_input_file.main(INPUT_FILE,preproc_cwd)

    currentmessage = ('\nStarting update_wellpkg_nfseg_modified.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    # Argumnet provides the correct map projection
    update_wellpkg_nfseg_modified.main(mapproj,preproc_cwd,gis_dir)



    currentmessage = ('\nStarting create_two_stress_period_wellpkg_input_file.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    create_two_stress_period_wellpkg_input_file.main(wel_file,preproc_cwd)

    #    Finished creating well pkg.

    # Print out the date and time of processing
    print (bscut.datetime())
    with open(logfile,'a') as lf: lf.write('{}'.format(bscut.datetime()))
    # -----------------------------------------------------


    # =====================================================
    # Setup and run MODFLOW
    # =====================================================

    #cd ..\..\model_update
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
    #bscut.copyfile(wel_file, os.path.join(model_dir,'nfseg_auto.wel'))
    #!!! LEFT HERE !!! PMB propagate continue
    #if not (bscut.copyfile('wel_file', os.path.join(model_dir,'nfseg_auto.wel'), logfile)): continue
    if not (bscut.copyfile(wel_file, os.path.join(model_dir,'nfseg_auto.wel'), logfile)): continue

    currentmessage = ('\nExecuting modflow. This may take a few moments . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)

    nam_file = os.path.join(model_dir,'nfseg_auto_2009.nam')
    
    if not bscut.modflow(mfexe_dir,model_dir,nam_file,logfile): continue
    #modflow-nwt_64.exe nfseg_auto_2009.nam
    
    # -----------------------------------------------------
    
    
    
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Copy MODFLOW results to postprocessing directories
    # TODO: Change the functions to use one copied to the results directory
    if not (bscut.copyfile(os.path.join(model_dir,'nfseg_auto.lst')
                           ,os.path.join(postproc_dQ_results,'nfseg_auto.lst')
                           ,logfile)): continue
    #if not (bscut.copyfile(os.path.join(model_dir,'nfseg_auto.lst')
    #                       ,os.path.join(postproc_budget_cwd,'nfseg_auto.lst')
    #                       ,logfile)): continue
    
    if not (bscut.copyfile(os.path.join(model_dir,'nfseg_auto.hds')
                           ,os.path.join(postproc_dh_results,'nfseg_auto.hds')
                           ,logfile)): continue
    
    # Define a name for the list file output from MODFLOW after it is copied
    # to the results directory
    listfile = os.path.join(postproc_budget_results,'nfseg_auto.lst')
    
    # The results directory
    if not (bscut.copyfile(os.path.join(model_dir,'nfseg_auto.lst')
                           ,listfile
                           ,logfile)): continue
    
    # ---------------------------------------
    # Begin generating the budget check reports
    # ---------------------------------------

    currentmessage = ('\n\nGenerate budget check reports . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    

    #cd ..\postproc\budget
    
    # Name output files that will be recreated
    #budoutput = os.path.join(postproc_budget_cwd,'global_budget_change.csv')
    budoutput = D_global_budget_out
    rivfluxoutput = os.path.join(postproc_budget_results,'global_river_plus_drain_flux_changes.asc')
    #rivfluxoutput = os.path.join(postproc_budget_cwd,'global_river_plus_drain_flux_changes.asc')
    
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
    # Begin generating the change in flow reports
    # ---------------------------------------

    currentmessage = ('\n\ngenerate simulated river and spring flux change reports . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)

    #cd ..\dQ
    
    # Define some intermediate output filenames
    temp_shelf = os.path.join(postproc_dQ_results,'temp.shelf')
    cup_id_n_rate = os.path.join(postproc_dQ_results,'cup_id_and_rate.csv')
    
    # Delete files that will be created again, if they exist
    bscut.deletefile(temp_shelf,logfile)
    bscut.deletefile(cup_id_n_rate,logfile)
    
    if not (bscut.copyfile(os.path.join(preproc_cwd,'cup_id_and_rate.csv')
                           , cup_id_n_rate
                           , logfile)): continue
    
    currentmessage = ('\nStarting sim_q_reach_3d_auto.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    gaged_reach_flux_out = os.path.join(postproc_dQ_results,'gaged_reach_fluxes.asc')
    sim_q_reach_3d_auto.main(listfile,
                             mydef.ConvFactors().sec2day,
                             logfile,
                             postproc_deffiles_dQ,
                             postproc_dQ_results,
                             gaged_reach_flux_out)
    
    currentmessage = ('\nStarting sum_sim_q_reach.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    gaged_flux_sum_output = os.path.join(postproc_dQ_results,'gaged_fluxes_sum.csv')
    sum_sim_q_reach.main(logfile,
                         postproc_deffiles_dQ,
                         gaged_reach_flux_out,
                         gaged_flux_sum_output)
    

    currentmessage = ('\nStarting create_delta_q_report.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    create_delta_q_report.main(logfile,
                               postproc_deffiles_dQ,
                               cup_id_n_rate,
                               gaged_reach_flux_out,
                               gaged_flux_sum_output,
                               DQ_summary_out)
    # =======================================


    # ---------------------------------------
    # Begin generating the change in heads report
    # ---------------------------------------

    currentmessage = ('\n\nGenerate simulated head change maps . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)

    #cd ..\dH
    
    # Postprocess using PEST utilities
    
    
    # !!! LEFT OFF HERE !!! PMB
    many2one_infile = os.path.join(postproc_deffiles_dh,'many2one_layers1_and_3_hds_nfseg.inp')
    many2one_log = os.path.join(postproc_dh_results,'many2one.log')
    bscut.deletefile(many2one_log, logfile)
    if not bscut.many2one(src_postprocess_dir,many2one_infile,many2one_log,postproc_dh_results,logfile): continue
    #many2one < many2one_layers1_and_3_hds_nfseg.inp > many2one_log
    
    
    twoarray_infile_lay1 = os.path.join(postproc_deffiles_dh,'twoarray_dh_layer1_nfseg.inp')
    twoarray_infile_lay3 = os.path.join(postproc_deffiles_dh,'twoarray_dh_layer3_nfseg.inp')
    twoarray_lay1_log = os.path.join(postproc_dh_results,'twoarray_dh_layer1.log')
    twoarray_lay3_log = os.path.join(postproc_dh_results,'twoarray_dh_layer3.log')
    bscut.deletefile(twoarray_lay1_log,logfile)
    bscut.deletefile(twoarray_lay3_log,logfile)
    if not bscut.twoarray(src_postprocess_dir,twoarray_infile_lay1,twoarray_lay1_log,postproc_dh_results,logfile): continue
    if not bscut.twoarray(src_postprocess_dir,twoarray_infile_lay3,twoarray_lay3_log,postproc_dh_results,logfile): continue
    #twoarray < twoarray_dh_layer1_nfseg.inp > twoarray_lay1_log
    #twoarray < twoarray_dh_layer3_nfseg.inp > twoarray_lay3_log
    
    
    # TODO: These deletions need to be moved into the ReadModflowFloatArrays function
    dh_lyr1_tableFormat = os.path.join(postproc_dh_results,'dh_lyr1_tableFormat.csv')
    dh_lyr3_tableFormat = os.path.join(postproc_dh_results,'dh_lyr3_tableFormat.csv')
    bscut.deletefile(dh_lyr1_tableFormat,logfile)
    bscut.deletefile(dh_lyr3_tableFormat,logfile)
    
    array_spec_in = os.path.join(postproc_deffiles_dh,'array_reader.spc')
    array_file_names_in = os.path.join(postproc_deffiles_dh,'sim_head_arrays_file_names.asc')
    
    currentmessage = ('\n\nStarting ReadModflowFloatArrays.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    ReadModflowFloatArrays.main(postproc_dh_results, array_spec_in, array_file_names_in, logfile)
    # =======================================


    # ---------------------------------------
    # Update the map project and finalize
    # ---------------------------------------

    # echo cd ..\..\gis
    # echo del dh.mxd
    # echo copy dh_template.mxd dh.mxd

    # Need to delete the old dh.gdb directory before running make_ArcGIS_table_from_csv.py !!! PMB

    currentmessage = ('\n\nStarting make_ArcGIS_table_from_csv.py . . .\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    make_ArcGIS_table_from_csv.main()  # !!! PMB !!! Need to pass logfile into function


    currentmessage = ('\n\tCompleted dh processing\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    # =======================================

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


    # =====================================================
    # Copy the reports to the top-level directory.
    # Change the names of the reports to carry
    # the basename of the input file.
    # =====================================================
    
    # Name the two output csv files
    #Global_bud = os.path.join(postproc_budget_cwd,'global_budget_change.csv')
    #deltaQ = os.path.join(postproc_dQ_cwd,'delta_q_summary.csv')
    
    #if not (bscut.copyfile(deltaQ, DQ_summary_out, logfile)): continue
    #if not (bscut.copyfile(Global_bud, D_global_budget_out, logfile)): continue

    currentmessage = ('\n\nResults have been written to the summary reports:\n' +
                      DQ_summary_out +
                      D_global_budget_out)
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)


    currentmessage = ('\n\nPROCESSING COMPLETE. . .\n' +
                      'IF NO ERROR OR WARNING MESSAGES APPEAR IN ' +
                      'THE CONSOLE THEN THE SIMULATION WAS SUCCESSFUL!\n\n')
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
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%