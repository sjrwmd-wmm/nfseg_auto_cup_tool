import shelve
import copy

# open reach-lookup shelve file from calibration
book = shelve.open('lookup_bc_reach_ids.shelf')
reach_ids = book['reach_ids']
reach_ids_from_2d_ids = book['reach_ids_from_2d_ids']
book.close()

# open a new reach-lookup shelve file for storing data
#    from second stress period in both stress periods
book_auto = shelve.open('lookup_bc_reach_ids_auto.shelf')
reach_ids_auto = {}

for temp_key in reach_ids.keys():
        bc, sp = temp_key
        reach_ids_auto[(bc, sp)] = reach_ids[(bc, 2)]

book_auto['reach_ids'] = reach_ids_auto

reach_ids_from_2d_ids_auto = {}

for temp_key in reach_ids_from_2d_ids:
    bc, sp = temp_key
    reach_ids_from_2d_ids_auto[(bc, sp)] = reach_ids_from_2d_ids[(bc, 2)]

book_auto['reach_ids_from_2d_ids'] = reach_ids_from_2d_ids_auto
book_auto.close()
