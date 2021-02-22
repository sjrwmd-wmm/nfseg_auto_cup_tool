# Convert NFSEG v1.1 reach ID shelf files to ascii txt
# 
# NOTE: Shelf files do not cross Python versions well.
#       If the shelf file was made in Python2.7, then
#       use Python2.7 to convert it
#
# NOTE: Shelf files are binary Python dictionary files.
#       Items contained in the dictionary list do not have
#       an intrinsic order (not alpha-numeric, ascending, etc.),
#       nor is the dictionary's at-time-of-writing order preserved.
#       However, key:value pairs remain intact. Any desired order
#       must be done at runtime within the program reading
#       the shelf file.
#
#
# To use this script:
#     - Navigate to the directory containing the shelf files
#       that require conversion
#     - Uncomment one of the lines below that set the
#       inputf (input file) variable to the desired input file
#     - Run script using command-line call to Python2.7
#       (see note above). ArcMap 10.X Python2.7 is sufficient.
#       Example:
#       C:\Python27\ArcGIS10.6\python <PATH-TO-SCRIPT>\shelf2txt.py
#
#
# This script reads a shelf file created for the NFSEG v1.1
# groundwater model and converts it to multiple ascii csv files.
# The data contained in the shelf file is distributed to files
# according to its boundary condition type.
#
# Written 20201217. PMBremner


import shelve
import pandas as pd

# ****************************
# Select the input binary file
# - Uncomment selection
# - Comment others
# ****************************
#inputf = 'lookup_bc_reach_ids.shelf'; option = 1
inputf = 'lookup_bc_reach_ids_auto.shelf'; option = 1
#inputf = 'bc_fluxes.shelve'; option = 2
# ****************************


# Output ascii txt file
outputf_prefix = ('.'.join(inputf.split('.')[:-1]) + '.')


print('Converting {} output to ascii\n\n'.format(inputf))


# Open the shelf file and associate contents to variable
book = shelve.open(inputf)


# Read in all the available keys
my_keys = list(book.keys())

# Shelf file insorted, need to sort them somehow
my_keys.sort()

# TODO: Rewrite this section like the second section !!!
# Output dictionary data to separate files according to data type
# Option variable is used to distinquish between shelf file
# data organization.
if (option==1):
    
    # Upon manual inspection, the shelf file contains
    # two main dictionary keys: ['reach_ids', 'reach_ids_from_2d_ids']
    #
    # The 'reach_ids' key contains six subkeys made up of a
    # tuple of boundary condition and stress period:
    # [('ghb', 1), ('ghb', 2), ('riv', 1), ('riv', 2), ('drn', 1), ('drn', 2)]
    # Each subkey contains a simple list of bc_reach_id's,
    # which are boundary condition reach id numbers from the
    # package file. No other information is contained in this.
    #
    # For the 'reach_ids_from_2d_ids' key, each subkey contains
    # two subkeys: [('riv', 1), ('riv', 2)].
    # Each subkey contains a series of dictionary sub-subkeys
    # that represent the bc_2d_reach_id, which are the boundary
    # condition 2d reach id numbers from the river package file.
    # Each of these sub-subkeys contains a list of associated
    # bc_reach_id numbers from the same package file.
    
    curkey = 'reach_ids'
    
    # Run through all the data to collect the datatypes.
    # Use a dictionary as a way to efficiently collect
    # the types without repeat. A bogus value will be
    # set just to create the dictionary, but will not
    # be used later.
    #
    # Define file names for all the datatypes.
    # Use a dictionary list to store them.
    # Also initialize a dictionary for the dataframe.
    fout = {}
    datarows = {}
    for subkey in book[curkey].keys():
        # Grab the current datatype from the tuple
        curtype = subkey[0]
        
        # Check if a key already exists by trying to set its value.
        # If it doesn't exist, add it.
        if not curtype in datarows:
            fout.update({curtype:(outputf_prefix + curkey + '_' + curtype + '.csv')})
            datarows.update({curtype:{}})
        #
    #
    
    # Run through the data a second time to create a dataframe
    # of the values. The columns will be defined by
    # stress_period. The rows will defined by bc_reach_id.
    idname = 'bc_reach_id'
    for subkey in book[curkey].keys():
        # Parse the tuple contained in the key
        #
        # Grab the current datatype from the tuple
        curtype = subkey[0]
        #
        # Grab the current stress period
        cur_sp = ('SP' + str(subkey[1]))
        if (curtype=='riv'): cur_2d_id = (cur_sp+'_2d_id')
        #
        
        for cur_id in book[curkey][subkey]:
            # Add the items to a current data dictionary list
            # then add the info to the datarow. Must check
            # if the datarow already exists first.
            if cur_id in datarows[curtype]:
                if cur_sp not in datarows[curtype][cur_id]:
                    if (curtype=='riv'):
                        datarows[curtype][cur_id].update({cur_sp:'x', cur_2d_id:""})
                    else:
                        datarows[curtype][cur_id].update({cur_sp:'x'})
                    #
                else:
                    error_message = 'Multiple bc_reach_ids for one dataframe coordinate: {0}\nDataType {1} and reach_id {2}\n'.format(datarows[curtype][cur_id][cur_sp],curtype,cur_id)
                    raise KeyError(error_message)
            else:
                if (curtype=='riv'):
                    curdata = {idname:cur_id, cur_sp:'x', cur_2d_id:""}
                else:
                    curdata = {idname:cur_id, cur_sp:'x'}
                datarows[curtype].update({cur_id:curdata})
            #
        #
    #
    
    # ---------------------
    # Now grab all the River BC 2d reach ids to associate to the reach ids
    # ---------------------
    
    curkey = 'reach_ids_from_2d_ids'
    
    for subkey in book[curkey].keys():
        # Parse the tuple contained in the key
        #
        # Grab the current datatype from the tuple
        curtype = subkey[0]
        #
        # Grab the current stress period
        cur_sp = ('SP' + str(subkey[1]))
        cur_2d_id = (cur_sp+'_2d_id')
        #
        
        # March through the entire list of entries
        for subsubkey,cur_2d_id_list in book[curkey][subkey].items():
            for cur_id in cur_2d_id_list:
                #print (datarows[curtype][cur_id])
                # Add the 2d reach id to the associated reach id
                if cur_2d_id in datarows[curtype][cur_id]:
                    datarows[curtype][cur_id][cur_2d_id] = subsubkey
                else:
                    error_message = 'Missing 2d reach data column: Current reach id {0}, Current stress period {1}, and 2d reach id {2}\n'.format(cur_id, cur_sp, subsubkey)
                    raise KeyError(error_message)
                #
            #
        #
    #
    
    # Loop through the datatypes.
    # Place the appropriate datarows in a data list.
    # Create a dataframe a save to file
    for key in fout.keys():
        
        # Grab the datarows for the current datatype
        data = list(datarows[key].values())
        
        # Put the data into a pandas dataframe
        df = pd.DataFrame(data)
        
        # Make a quick correction to the order of the df
        if (curtype=='riv'):
            cols = ['bc_reach_id', 'SP1', 'SP1_2d_id', 'SP2', 'SP2_2d_id']
            #cols = ['bc_reach_id', 'SP1', 'SP1_2d_id', 'SP2', 'SP2_2d_id']
        else:
            cols = ['bc_reach_id','SP1','SP2']
        #
        # Move the bc_reach_id to the first column from the last column
        cols = df.columns.tolist()
        cols = cols[-1:]+cols[:-1]
        df = df[cols]
        
        # Output dataframe to file
        df.to_csv(path_or_buf=fout[key], sep=',', na_rep='', header=True, index=False, mode='w', encoding='utf-8', compression=None, line_terminator='\n', errors='strict')
    #
    # ---------------------
    
elif (option==2):
    
    # Upon manual inspection, the shelve file contains
    # two main dictionary keys: ['bc_fluxes', 'bc_list']
    #
    # First create and output a dataframe of the bc_fluxes data.
    # Second, check that the reach_id's listed in bc_list
    # are also contained in bc_fluxes.
    # If the reach_id lists are the same, then only the
    # bc_fluxes reach_id's and data need to be output.
    
    curkey = 'bc_fluxes'
    
    # Data stored in a dictionary where each key is a tuple.
    # The first element of the tuple is the datatype string.
    # Tuple format: (datatype, bc_reach_id, stress_period, time_step)
    
    # Run through all the data to collect the datatypes.
    # Use a dictionary as a way to efficiently collect
    # the types without repeat. A bogus value will be
    # set just to create the dictionary, but will not
    # be used later.
    datatype = {}
    for key in book[curkey].keys():
        # Grab the current datatype from the tuple
        curtype = key[0]
        # Check if a key already exists by trying to set its value.
        # If it doesn't exist, add it.
        try:
            datatype[curtype] = 0
        except KeyError:
            datatype.update({curtype:0})
        #
    #
    # Define file names for all the datatypes.
    # Use a dictionary list to store them.
    # Also initialize a dictionary for the dataframe.
    fout = {}
    datarows = {}
    for key in datatype.keys():
        fout.update({key:(outputf_prefix + curkey + '_' + key + '.csv')})
        datarows.update({key:{}})
    #
    
    # Run through the data a second time to create a dataframe
    # of the values. The columns will be defined as a join of
    # (stress_period)_(time_step). The rows will defined by
    # bc_reach_id. Flux will be the value at each coordinate.
    # Use a dictionary 'datarows' as a way to combine the
    # data from each stress_period and time_step into
    # a single row entry in the dataframe.
    idname = 'bc_reach_id'
    for key,value in book[curkey].items():
        # Parse the tuple contained in the key
        #
        # Grab the current datatype from the tuple
        curtype = key[0]
        #
        # Grab the current bc_reach_id
        cur_id = key[1]
        #
        # Grab the current stress_period, time_step combo
        cur_spts = ('SP' + str(key[2]) + '_TS' + str(key[3]))
        
        # Add the items to a current data dictionary list
        # then add the info to the datarow. Must check
        # if the datarow already exists first.
        if cur_id in datarows[curtype]:
            if cur_spts not in datarows[curtype][cur_id]:
                datarows[curtype][cur_id].update({cur_spts:value})
            else:
                error_message = 'Multiple values for one dataframe coordinate: {0} {1}\nDataType {2} and reach_id {4}\n'.format(datarows[curtype][cur_id][cur_spts],value,curtype,cur_id)
                raise KeyError(error_message)
        else:
            curdata = {idname:cur_id, cur_spts:value}
            datarows[curtype].update({cur_id:curdata})
        #
    #
    # Loop through the datatypes.
    # Place the appropriate datarows in a data list.
    # Create a dataframe a save to file
    for key in fout.keys():
        
        # Grab the datarows for the current datatype
        data = list(datarows[key].values())
        
        # Put the data into a pandas dataframe
        df = pd.DataFrame(data)
        
        # Make a quick correction to the order of the df
        # Move the bc_reach_id to the first column from the last column
        cols = df.columns.tolist()
        cols = cols[-1:]+cols[:-1]
        df = df[cols]
        
        # Output dataframe to file
        df.to_csv(path_or_buf=fout[key], sep=',', na_rep='', header=True, index=False, mode='w', encoding='utf-8', compression=None, line_terminator='\n', errors='strict')
    #
    
    
    curkey = 'bc_list'
    
    # Capture the list of datatype key values
    datatype_keys = list(book[curkey].keys())
    
    # March through the data from each datatype key.
    # Check that bc_list and bc_fluxes have the same
    # list of bc_reach_id's.
    # Ensure the number of data items are the same,
    # then ensure each bc_reach_id is found in both
    # lists of data.
    for key in datatype_keys:
        if not (len(book[curkey][key]) == len(datarows[key])):
            error_message = 'Mismatch in data length: {}'.format(key)
            raise Exception(error_message)
        #
        
        for cur_id in book[curkey][key]:
            if cur_id not in datarows[key]:
                error_message = 'Reach ID {} was not present in both lists. Data type {}\n'.format(cur_id,key)
                raise KeyError(error_message)
            #
    #
    
#

# All data processed...close the file
book.close()
