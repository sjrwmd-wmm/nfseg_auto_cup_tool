!====================================================================
!
! Read in nfseg simulated heads 
! Extract and evaluated area weighted average UFA heads beneath lakes
! Export extracted heads for SP1 and SP2
!
! Requires an Input Control File in the current directory for input control
!
! Code written in standard Fortran 2008
!
! Compile with:
! --- (on Windows)
! LGF nfseg_extract_modelwide_and_lake_hds.f08 -out nfseg_extract_modelwide_and_lake_hds.exe
! --- (on Linux)
! gfortran nfseg_extract_modelwide_and_lake_hds.f08 -o nfseg_extract_modelwide_and_lake_hds.exe
!
!====================================================================



! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
!
! GLOBAL DEFINITION MODULE
!
! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

MODULE GlobalDef
    
    ! Import the ISO Frotran 2008 standard environment
    use ISO_Fortran_env
    !use ISO_C_Binding ! From Fortran 2003
    
    !------------------------------
    ! Define global precision
    !------------------------------
    !
    ! Fortran 95 and later
    !selected_real_kind(['decimal precision', decimal exponent range'])
    !integer, parameter :: p8 = selected_real_kind( 8, 50 ) ! Fortran 95 and later
    !
    ! Fortran 90
    !integer, parameter :: SP = KIND( 1.0 ) ! Single Precision Float
    !integer, parameter :: DP = KIND( 1.0D0 ) ! Double Precision Float
    !
    ! Fortran 2003 standard
    !integer, parameter :: SP = c_float ! Single Precision Float
    !integer, parameter :: DP = c_double ! Double Precision Float
    !
    ! Fortran 2008 standard
    integer ( int32 ), parameter :: I32 = int32 ! 32 Bit (4 byte) Integer
    integer ( int32 ), parameter :: I64 = int64 ! 64 Bit (8 byte) Integer
    integer ( int32 ), parameter :: R32 = real32 ! 32 Bit (4 byte) Single Precision Float
    integer ( int32 ), parameter :: R64 = real64 ! 64 Bit (8  byte) Double Precision Float
    !------------------------------
END MODULE GlobalDef



! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
!
! GENERAL UTILITIES MODULE
!
! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

MODULE GeneralUtilities
    
    ! Import the ISO Frotran 2008 standard environment
    use ISO_Fortran_env
    
    ! Import the Global Definitions
    use GlobalDef
    
    CONTAINS

    ! A function that converts an integer to a string
    ! Function found as part of an answer on stackoverflow on 20201201:
    ! https://stackoverflow.com/questions/1262695/convert-integers-to-strings-to-create-output-filenames-at-run-time
    FUNCTION itoa(i) RESULT(res)
        !use ISO_Fortran_env
        implicit none
        character(:),allocatable :: res
        integer(I32),intent(in) :: i
        character(range(i)+2) :: tmp
        WRITE (tmp,'(i0)') i
        res = TRIM(tmp)
    END FUNCTION itoa
    
    
    ! Subroutine to convert a string to an integer
    ! Inspired by an answer on stackoverflow on 20201207:
    ! https://stackoverflow.com/questions/24071722/converting-a-string-to-an-integer-in-fortran-90
    SUBROUTINE str2int32(str, newint, status)
        implicit none
        character(len=*), intent(in) :: str
        integer(I32), intent(out) :: newint
        integer(I32), intent(out) :: status
        
        read(str, *, iostat=status) newint
    END SUBROUTINE str2int32
    
    
    ! A subroutine to find the array index of an array value that
    ! matches an input string.
    ! index_val is returned as a positive integer corresponding to
    ! the index value, or -1 if no matches were found.
    ! This subroutine returns the index of the first match found.
    ! This uses a brute force method to find matches in the array,
    ! and could be made more sofiticated, such as using the
    ! intrinsic FINDLOC function implemented as part of
    ! Fortran 2008. That was unavailable at the time of writing this.
    SUBROUTINE find_index_char(array, string, strlen, index_val)
        !use ISO_Fortran_env
        implicit none
        integer(I32), intent(in) :: strlen
        character (len=strlen), dimension (:), intent(in) :: array
        character (len=strlen), intent(in) :: string
        integer(I32), intent(out) :: index_val
        integer(I32) :: i
        
        ! Initialize the return value to negative one
        index_val = -1
        
        checkval: DO i = 1, SIZE(array)
            IF (array(i).EQ.string) THEN
                ! Found a match, set the value and exit
                index_val = i
                EXIT checkval
            END IF
        END DO checkval
    END SUBROUTINE find_index_char
END MODULE GeneralUtilities



! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
!
! MODFLOW SUBROUTINES MODULE
!
! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

MODULE modflowsubs
    
    ! Import the ISO Frotran 2008 standard environment
    use ISO_Fortran_env
    
    ! Import the Global Definitions and other useful modules
    use GlobalDef
    use GeneralUtilities
    
    CONTAINS
    
    
    SUBROUTINE read_modflow_heads(hds_file, hfilename_length, hds, kper, kstp, nlay, ncol, nrow)
        
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        !
        ! Declare subroutine variables
        !
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        
        implicit none
        

        ! Error control and file units
        integer(I32) :: ioerr, fin
        
        
        ! Specify the heads filename and name length
        integer (I32), intent(in) :: hfilename_length
        character(len=hfilename_length), intent(in) :: hds_file
        
        
        ! TODO: Make the final 3 variables as optional outputs
        !------------------------------
        ! Specify heads file parameters
        !------------------------------
        ! From the MODFLOW 2000 documentation
        ! The array data can be either in single-precision or
        ! double-precision format.  There is no data field that
        ! indicates which format is used.  Instead, you will
        ! need to try both and see which one works.
        integer ( I32 ), intent(out) :: kstp ! the time step number, 4 byte integer
        integer ( I32 ), intent(out) :: kper ! the stress period number, 4 byte integer
        !real ( R32 ) :: pertim ! the time in the current stress period, either 4 or 8 byte real number
        !real ( R32 ) :: totim ! the total elapsed time, either 4 or 8 byte real number
        character( len = 16 ) :: desc ! a description of the array, 16 ANSI characters, 16 bytes.
        integer ( I32 ), intent(out) :: ncol ! the number of columns in the array, 4 byte integer
        integer ( I32 ), intent(out) :: nrow ! the number of rows in the array, 4 byte integer
        ! Next come a list of NROW x NCOL real numbers that represent the
        ! values of the array. The values are in row major order. Each
        ! value in the array occupies either 4 or 8 bytes depending on
        ! whether the values are in single- or double-precision.
        !real ( R32 ), dimension ( :, :, :, : ) :: hds( ncol, nrow, nlay, nsp )
        real ( R32 ), dimension ( :, :, :, :, : ), allocatable, intent(out) :: hds !kper, kstp, nlay, ncol, nrow
        !------------------------------
        
        ! Additional definitions and current read variables
        integer ( I32 ), intent(out) :: nlay ! number of layers, 4 byte integer
        integer ( I32 ) :: cur_kstp, cur_kper
        integer ( I32 ) :: cur_row, cur_col, cur_lay
        real ( R32 ) :: cur_pertim, cur_totim
        real( R32 ) :: dummy
        
        ! These integers must be 4 bytes in length
        integer ( I64 ) :: i, n
        
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        !
        ! Begin processing the heads file
        !
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        
        ! Read the HDS file to obtain the array size information
        OPEN ( NEWUNIT = fin, FILE = TRIM(hds_file), FORM = 'unformatted', STATUS = 'old' &
                , ACCESS = 'stream', IOSTAT = ioerr, ACTION = 'read' )
        IF ( ioerr .ne. 0 ) THEN
            WRITE(output_unit,9001) "ERROR",ioerr,"Problem opening",ADJUSTL(TRIM(hds_file))
            9001 FORMAT (A,1X,I0,/,A,1X,A)
            STOP
        END IF
        
        ! Initialize model properties
        kstp = 0
        kper = 0
        ncol = 0
        nrow = 0
        nlay = 0

        hdr1: DO
                READ ( fin, IOSTAT = ioerr ) cur_kstp, cur_kper, cur_pertim, cur_totim, desc, cur_col, cur_row, cur_lay
                
                ! Exit the loop when EOF reached
                IF ( ioerr .eq. iostat_end ) EXIT hdr1
                
                ! Ensure the data is HEADS data
                IF ( ADJUSTL(TRIM(desc)) .NE. "HEAD" ) THEN
                    WRITE (output_unit,9002) "ERROR", &
                                             "Data is not designated as HEAD", &
                                             "File",TRIM(hds_file), &
                                             "Stress Period",cur_kper,"Time Step",cur_kstp,"Layer",cur_lay
                    9002 FORMAT (A,/,A,/,A,1X,A,/,A,1X,I0,2X,A,1X,I0,2X,A,1X,I0)
                    STOP
                END IF
                
                WRITE (output_unit,*) cur_kstp, cur_kper, cur_pertim, cur_totim, desc, cur_col, cur_row, cur_lay

                ! Update the maximum values
                IF ( kstp .LT. cur_kstp ) kstp = cur_kstp
                IF ( kper .LT. cur_kper ) kper = cur_kper
                IF ( ncol .LT. cur_col ) ncol = cur_col
                IF ( nrow .LT. cur_row ) nrow = cur_row
                IF ( nlay .LT. cur_lay ) nlay = cur_lay

                
                ! Calculate the product of rows and columns, loop through n
                n = cur_row * cur_col
                DO i = 1,n
                    READ ( fin ) dummy ! file seek instead of read?
                END DO
        END DO hdr1
        

        WRITE (output_unit,*) kper, kstp, nlay, ncol, nrow
        
        ! Allocate hds array memory
        ALLOCATE ( hds( kper, kstp, nlay, ncol, nrow ) )


        ! Rewind the file and actually read the hds values this time
        REWIND ( fin )

        hdr2: DO
                READ ( fin, IOSTAT = ioerr ) cur_kstp, cur_kper, cur_pertim, cur_totim, desc, cur_col, cur_row, cur_lay
                
                ! Exit the loop when EOF reached
                IF ( ioerr .eq. iostat_end ) EXIT hdr2
                
                ! Read values for all the columns and rows at the current SP, timestep, and layer
                READ ( fin, IOSTAT = ioerr ) hds( cur_kper, cur_kstp, cur_lay, :, : )
                IF ( ioerr .NE. 0 ) THEN
                    WRITE (output_unit,9003) "ERROR",ioerr, &
                                          "Problem reading hds values at:", &
                                          "Stress Period",cur_kper,"Time Step",cur_kstp,"Layer",cur_lay
                    9003 FORMAT (A,1X,I0,/,A,/,A,1X,I0,2X,A,1X,I0,2X,A,1X,I0)
                    STOP
                END IF
        END DO hdr2
        CLOSE ( fin )
        
    END SUBROUTINE read_modflow_heads
    
    
    
    SUBROUTINE delta_head_modelwide(nlay, nrow, ncol, per_b, stp_b, per_a, stp_a, deltaH_f, hds)
        
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        !
        ! Declare subroutine variables
        !
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        
        implicit none
        

        ! Error control and file units
        integer(I32) :: ioerr, fout
        
        integer ( I32 ), intent(in) :: ncol, nrow, nlay
        integer ( I32 ), intent(in) :: per_b, stp_b, per_a, stp_a
        character(len=*), intent(in) :: deltaH_f
        
        ! Allocated as hds(kper, kstp, nlay, ncol, nrow)
        real ( R32 ), dimension ( :, :, :, :, : ), allocatable, intent(in) :: hds
        
        
        ! Additional definitions and current read variables
        integer ( I32 ) :: cur_row, cur_col, cur_lay
        
        
        ! Define deltaH file variables
        integer ( I32 ) :: seqnum
        real ( R32 ) :: head_diff
        character (:), allocatable :: layerstr
        
        
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        !
        ! Calculate laterally modelwide cell-wise
        ! head differences for each model layer
        !
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        
        
        OPEN ( NEWUNIT = fout, FILE = deltaH_f, FORM = 'formatted' &
                , STATUS = 'replace', ACTION = 'write', ACCESS = 'sequential', IOSTAT = ioerr )
        IF ( ioerr .ne. 0 ) THEN
            WRITE(output_unit,9001) "ERROR",ioerr,"Problem opening",ADJUSTL(TRIM(deltaH_f))
            9001 FORMAT (A,1X,I0,/,A,1X,A)
            STOP
        END IF
        
        ! Write out a header
        WRITE (fout,'(A)',advance='no') "Row Col SeqNum"
        DO cur_lay=1,nlay,1
            ! Make the layer value a string for easier formatting
            layerstr = itoa(cur_lay)
            
            IF (cur_lay .LT. nlay) THEN
                WRITE (fout,'(1X,A,A)',advance='no') "Layer",layerstr
            ELSE
                WRITE (fout,'(1X,A,A)',advance='yes') "Layer",layerstr
            END IF
        END DO
        
        DO cur_row = 1, nrow
            DO cur_col = 1, ncol
                DO cur_lay = 1, nlay
                    ! Calculate dH
                    head_diff = hds(per_b, stp_b, cur_lay, cur_col, cur_row) - hds(per_a, stp_a, cur_lay, cur_col, cur_row)
                    
                    ! Calculate the sequence number for easy GIS incorporation
                    seqnum = (cur_row-1)*ncol + cur_col
                    
                    ! Write output
                    ! NOTE Only print the row, column, sequence number once for each data row
                    IF (cur_lay .EQ. 1) THEN
                        WRITE (fout,'(I0,1X,I0,1X,I0,1X,G0.6)',advance='no') cur_row, cur_col, seqnum, head_diff
                    ELSE IF (cur_lay .EQ. nlay) THEN
                        WRITE (fout,'(1X,G0.6)',advance='yes') head_diff
                    ELSE
                        WRITE (fout,'(1X,G0.6)',advance='no') head_diff
                    END IF
                END DO
            END DO
        END DO
        
        CLOSE(fout)
        
    END SUBROUTINE delta_head_modelwide
    
    
    
    SUBROUTINE avg_lakehead_n_diff(kstp, kper, nlay, per_b, stp_b, per_a, stp_a, infile, outfile_prefix, hds)
        
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        !
        ! Declare subroutine variables
        !
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        
        implicit none
        
        character ( len = * ), intent(in) :: infile, outfile_prefix
        integer ( I32 ), intent(in) :: kstp, kper, nlay
        integer ( I32 ), intent(in) :: per_b, stp_b, per_a, stp_a
        
        ! Allocated as hds(kper, kstp, nlay, ncol, nrow)
        real ( R32 ), dimension ( :, :, :, :, : ), allocatable, intent(in) :: hds
        
        
        ! Error control and file units
        integer(I32) :: ioerr, fin, fout
        
        ! Counting variables
        integer (I32) :: filelinecnt, counter
        integer ( I32 ) :: cur_kstp, cur_kper, cur_lake
        integer ( I32 ) :: cur_row, cur_col, cur_lay
                
        ! Lake definitions
        integer ( I32 ) :: lakeID, result_loc
        
        real ( R32 ) :: head_diff, arearatio
        real ( R32 ), dimension ( :, :, :, : ), allocatable :: lakehds
        
        integer ( I32 ), parameter :: lakeIDstrlen=25
        character ( len = lakeIDstrlen ) :: lakeID_str
        character ( len = lakeIDstrlen ), dimension( : ), allocatable :: lakeID_label
        character ( len = 15 ) :: layer_suffix="_layer_", suffix=".txt"
        character ( : ), allocatable :: outfile, outheader
        
        
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        !
        ! Average heads over lake area for each lake
        ! Find delta H for each lake
        !
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        
        
        ! Define a header line for the output files
        outheader = "LakeID UFA_Head_SP1 UFA_Head_SP2 SP2-SP1"
        
        
        ! Read in lake information
        OPEN ( NEWUNIT = fin, FILE = TRIM(infile), FORM = 'formatted' &
                , STATUS = 'old', ACTION = 'read', ACCESS = 'sequential', IOSTAT = ioerr )
        IF ( ioerr .ne. 0 ) THEN
            WRITE(output_unit,9001) "ERROR",ioerr,"Problem opening",ADJUSTL(TRIM(infile))
            9001 FORMAT (A,1X,I0,/,A,1X,A)
            STOP
        END IF

        READ ( fin, * ) ! Skip header line
        
        ! Initialize the counter
        filelinecnt = 0
        
        ! Read through the file first time to assess the number of lake cells
        ! For now assume the number of lakes and lake cells are equal -- the max case
        lakes_count: DO
            READ ( fin, *, IOSTAT = ioerr ) lakeID, cur_row, cur_col, arearatio
            
            ! Exit the loop when EOF reached
            !IF ( ioerr .eq. iostat_end ) EXIT lakes_count
            IF (ioerr .GT. 0) THEN
                WRITE(output_unit,9002) "ERROR ", ioerr, &
                                        "Problem reading the lake file:", TRIM(infile), &
                                        "Line number:",(filelinecnt+2) ! add 2 to account for the header and problem line
                9002 FORMAT (A,1X,I0,/,A,1X,A,/A,1X,I0)
                STOP
            ELSE IF (ioerr .EQ. iostat_end) THEN
                ! End of File...Exit the loop
                EXIT lakes_count
            ELSE
                ! Increment the counter
                filelinecnt = filelinecnt + 1
            END IF
        END DO lakes_count
        
        
        ! Allocate memory for the lake properties arrays
        ! WARNING Reallocation of these arrays seems to cause something that acts
        !         like a memory leak. Need to find better way of doing this allocation.
        !         For now the arrays must be explicitly initialized and deallocated
        !         at the end of this function.
        ALLOCATE ( lakehds( kper, kstp, nlay, filelinecnt ) )
        ALLOCATE ( lakeID_label(filelinecnt) )
        !print *, size(lakeID_label)
        !print *, size(lakehds)
        lakehds(:,:,:,:) = 0.0
        lakeID_label(:) = 'A'
        
        
        ! Initialize arrays for the current lake file and the counter
        cur_lake = 0
        counter = 0
        
        
        ! Rewind the file
        REWIND (fin)
        
        
        READ ( fin, * ) ! Skip header line
        
        ! March through data until EOF
        lakes1: DO
            READ ( fin, *, IOSTAT = ioerr ) lakeID, cur_row, cur_col, arearatio
            
            ! Exit the loop when EOF reached
            IF ( ioerr .eq. iostat_end ) EXIT lakes1
            
            ! Keep lakeID as string value separate from the lakehds array
            ! since it is possible for lakeID's to be nonsequential,
            ! to skip values, or even alpha-numeric
            !
            ! Convert to a string value
            lakeID_str = itoa(lakeID)
            
            
            ! Determine whether the lakeID is a repeat
            ! If a new ID is encountered, then increment the counter
            ! and add the label to the label array
            ! result will be positive int if location found, -1 otherwise
            !result_loc = FINDLOC(lakeID_label, lakeID_str)
            CALL find_index_char(lakeID_label, lakeID_str, lakeIDstrlen, result_loc)
            
            IF (result_loc .EQ. -1) THEN
                ! Increment the lake counter
                counter = counter + 1
                
                ! Set the current lake to the appropriate value
                cur_lake = counter
                
                ! Add the current lakeID
                lakeID_label(cur_lake) = lakeID_str
            ELSE IF (result_loc .GT. 0) THEN
                cur_lake = result_loc
            END IF
            
            ! Average the heads over lake area
            DO cur_kper = 1, kper
                DO cur_kstp = 1, kstp
                    DO cur_lay = 1, nlay
                        lakehds( cur_kper, cur_kstp, cur_lay, cur_lake ) = &
                                lakehds( cur_kper, cur_kstp, cur_lay, cur_lake ) &
                                + ( hds( cur_kper, cur_kstp, cur_lay, cur_col, cur_row ) * arearatio )
                    END DO
                END DO
            END DO
        END DO lakes1
        CLOSE ( fin )
        
        WRITE(output_unit,1000) "Current Lake File: ", TRIM(infile), "  NumSP ", kper &
                                , "  NumTS ", kstp, "  NumLakes ", counter, "  LakeCells ",filelinecnt
        1000 FORMAT (A,A,A,I0,A,I0,A,I0,A,I0)
        
        
        ! Output averaged head values
        DO cur_lay = 1, nlay
            
            ! Append prefix and suffixes to create the output filename
            outfile = &
                ADJUSTL(TRIM(outfile_prefix)) &
                //ADJUSTL(TRIM(layer_suffix))//itoa(cur_lay)//ADJUSTL(TRIM(suffix))
            
            OPEN ( NEWUNIT = fout, FILE = outfile, FORM = 'formatted' &
                    , STATUS = 'replace', ACTION = 'write', ACCESS = 'sequential', IOSTAT = ioerr )
            IF ( ioerr .ne. 0 ) THEN
                WRITE(output_unit,9003) "ERROR",ioerr,"Problem opening",ADJUSTL(TRIM(outfile))
                9003 FORMAT (A,1X,I0,/,A,1X,A)
                STOP
            END IF
            
            WRITE ( fout, '(A)' ) TRIM( outheader )
            
            DO cur_lake = 1, counter
                ! Get the head differences between stress periods and time steps
                ! TODO: Need efficient way to get all the differences between lots of things
                ! TODO: Format the output to save file size
                
                head_diff = lakehds( per_b, stp_b, cur_lay, cur_lake ) - lakehds( per_a, stp_a, cur_lay, cur_lake )
                
                WRITE ( fout, 1001 ) ADJUSTL(TRIM(lakeID_label(cur_lake))) &
                                , lakehds( per_a, stp_a, cur_lay, cur_lake ) &
                                , lakehds( per_b, stp_b, cur_lay, cur_lake ) &
                                , head_diff
                1001 FORMAT (A,1X,F0.7,1X,F0.7,1X,G0.8)
            END DO
            
            CLOSE ( fout )
        END DO
        
        ! WARNING Deallocate memory to prevent memory leaks for the next iteration
        DEALLOCATE (lakehds)
        DEALLOCATE (lakeID_label)
    
    END SUBROUTINE avg_lakehead_n_diff

END MODULE modflowsubs



! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
!
! MAIN PROGRAM
!
! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox

PROGRAM MAIN

    ! Import the ISO Frotran 2008 standard environment
    use ISO_Fortran_env ! From Fortran 2008
    
    
    ! Import the module of subroutines
    use GlobalDef
    use GeneralUtilities
    use modflowsubs

    implicit none
    
    
    ! Error control and file units
    integer(I32) :: ioerr, fin !, fout
    
    
    ! Parameters for the input control file
    character(len=100) :: control_file_tmp, TMP_ARG
    character(len=20) :: runmode
    character(:), allocatable :: control_file != "hds_processing_control_file.txt"
    integer (I32), parameter :: max_number_of_columns = 10, max_line_length = 1000
    integer (I32) :: line_index, filelinecnt, sectioncnt, i
    character(len=max_line_length) :: line
    character(len=300), dimension(max_number_of_columns) :: line_cols
    integer (I32) :: narg, arg, n_usage, n_prg_descrip, j
    character(len=1) :: dash_check
    logical :: skip_iteration, infile_check, runmode_check
    character(len=200), dimension(:), allocatable :: prg_descrip, usage
    
    
    ! Specify some model specific values
    integer (I32), parameter :: hds_filename_length = 100, hds_file_id_length = 5
    integer ( I32 ) :: n_hds_files
    character ( len = hds_file_id_length ), dimension ( : ), allocatable :: hds_file_id
    !character ( len = hds_file_id_length ) :: hds_file_id
    character ( len = hds_filename_length ), dimension ( : ), allocatable :: hds_file_list
    character(len=hds_filename_length) :: hds_file
    
    
    ! From the MODFLOW 2000 documentation
    ! The array data can be either in single-precision or
    ! double-precision format.  There is no data field that
    ! indicates which format is used.  Instead, you will
    ! need to try both and see which one works.
    integer ( I32 ) :: kstp ! the time step number, 4 byte integer
    integer ( I32 ) :: kper ! the stress period number, 4 byte integer
    integer ( I32 ) :: ncol ! the number of columns in the array, 4 byte integer
    integer ( I32 ) :: nrow ! the number of rows in the array, 4 byte integer
    ! Next come a list of NROW x NCOL real numbers that represent the
    ! values of the array. The values are in row major order. Each
    ! value in the array occupies either 4 or 8 bytes depending on
    ! whether the values are in single- or double-precision.
    ! Allocated as hds(kper, kstp, nlay, ncol, nrow)
    real ( R32 ), dimension ( :, :, :, :, : ), allocatable :: hds
    
    
    ! Additional definitions and current read variables
    integer ( I32 ) :: nlay ! number of layers, 4 byte integer
    
    
    ! Define deltaH file variables
    integer ( I32 ) :: per_b = 2, stp_b = 1, per_a = 1, stp_a = 1
    character ( len = 100 ) :: deltaH_filename_prefix, deltaH_filename
    character ( len = 15 ) :: layer_suffix="_layer_", suffix=".txt"
    
    
    ! Lake definitions
    integer ( I32 ) :: n_waterbodies_files, cur_waterbodies_file
    character ( len = 300 ), dimension ( : ), allocatable :: waterbodies_infile, waterbodies_outfile_prefix
    
    
    
    ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
    !
    ! PROCESS COMMAND-LINE ARGUEMENTS
    !
    ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
    
    
    ! =====================================================
    !
    ! Write the help documentation
    !    -- Program description
    !    -- Usage instructions
    !
    ! =====================================================
    n_prg_descrip = 9
    ALLOCATE(prg_descrip(n_prg_descrip))
    WRITE(prg_descrip(1),'(A)') "This program extracts an NFSEG simulated heads file"
    WRITE(prg_descrip(2),'(A)') "and calculates and outputs the following:"
    WRITE(prg_descrip(3),'(4X,A)') "- model-wide cell-wise change in heads for each model layer"
    WRITE(prg_descrip(4),'(4X,A)') "- area-weighted average heads beneath lakes for each model layer"
    WRITE(prg_descrip(5),'(2A)') NEW_LINE('A'),"Code written in standard Fortran 2008 and is compiled with:"
    WRITE(prg_descrip(6),'(4X,A)') "--- (on Windows)"
    WRITE(prg_descrip(7),'(A)') "LGF nfseg_extract_modelwide_and_lake_hds.f08 -out nfseg_extract_modelwide_and_lake_hds.exe"
    WRITE(prg_descrip(8),'(4X,A)') "--- (on Linux)"
    WRITE(prg_descrip(9),'(2A)') "gfortran nfseg_extract_modelwide_and_lake_hds.f08 -o nfseg_extract_modelwide_and_lake_hds.exe", &
    NEW_LINE('A')
    
    n_usage = 9
    ALLOCATE(usage(n_usage))
    WRITE(usage(1),'(3A)') NEW_LINE('A'),NEW_LINE('A'),"Program Usage:"
    WRITE(usage(2),'(A)') "'PATH'/'EXENAME' 'required command-line argument keys and inputs'"
    WRITE(usage(3),'(A)') "Required argument keys:"
    WRITE(usage(4),'(4X,A)') "'-in' Define the input-control-file name"
    WRITE(usage(5),'(4X,A)') "'-runmode' Defines whether the program run mode:"
    WRITE(usage(6),'(15X,A)') "'readonly' - read and print to screen the input-control-file data only"
    WRITE(usage(7),'(15X,A)') "'run' - read the input-control-file and process heads"
    WRITE(usage(8),'(A)') "Optional arguments:"
    WRITE(usage(9),'(4X,2A)') "'-h or --help' Prints help to the screen and ends the program",NEW_LINE('A')
    ! -----------------------------------------------------
    
    
    ! Retrieve the number of command-line arguments
    narg = command_argument_count()
    
    
    ! =====================================================
    !
    ! Check for flags and input file
    !
    ! =====================================================
    
    ! Initialize all the command-line option flags
    skip_iteration = .false.
    infile_check = .false.
    runmode_check = .false.
    
    IF (narg .LT. 1) THEN
        WRITE(output_unit,8001) "ERROR", &
            "Command-line arguments required, but none found!"
        WRITE(output_unit,'(A)') (TRIM(usage(j)),j=1,n_usage)
        8001 FORMAT (A,/,A)
    ELSE
        DO arg=1,narg
            IF (skip_iteration) THEN
                skip_iteration = .false.
                CYCLE ! skip the next iteration
            ELSE
                CALL get_command_argument(arg,TMP_ARG)
                IF (TMP_ARG .EQ. "-in") THEN
                    IF (narg .LT. (arg+1)) THEN
                        WRITE(output_unit,8002) "ERROR", &
                            "No Input Filename provided after -in!", &
                            "Check that the proper arguments are being supplied as '-key' 'input'"
                        WRITE(output_unit,'(A)') (TRIM(usage(j)),j=1,n_usage)
                        8002 FORMAT (A,/,A,/,A)
                        STOP
                    ELSE
                        CALL get_command_argument((arg+1),control_file_tmp)
                        WRITE(dash_check,'(A1)') control_file_tmp
                        IF (dash_check .EQ. "-") THEN
                            WRITE(output_unit,8003) "ERROR", "No input filename provided after -in!", &
                                "It is possible that the Input Filename begins with a dash ('-').", &
                                "A leading dash is reserved for command-line options. Ensure that", &
                                "the Input Filename provided does not begin with this character."
                            WRITE(output_unit,'(A)') (TRIM(usage(j)),j=1,n_usage)
                            8003 FORMAT (A,/,A,/,A,/,A,/,A)
                            STOP
                        ELSE
                            skip_iteration = .true. ! skip the next iteration
                            infile_check = .true. ! indicate that input file found
                            ALLOCATE (character(len=len_trim(control_file_tmp)) :: control_file)
                            control_file = ADJUSTL(TRIM(control_file_tmp))
                        END IF
                    END IF
                ELSE IF (TMP_ARG .EQ. "-runmode") THEN
                    IF (narg .LT. (arg+1)) THEN
                        WRITE(output_unit,8004) "ERROR", &
                            "No run mode provided after -runmode!", &
                            "Check that the proper arguments are being supplied as '-key' 'input'"
                        WRITE(output_unit,'(A)') (TRIM(usage(j)),j=1,n_usage)
                        8004 FORMAT (A,/,A,/,A)
                        STOP
                    ELSE
                        CALL get_command_argument((arg+1),runmode)
                        IF (runmode .EQ. 'readonly' .OR. runmode .EQ. 'run') THEN
                            skip_iteration = .true. ! skip the next iteration
                            runmode_check = .true. ! indicate that runmode found
                        ELSE
                            WRITE(output_unit,8005) "ERROR", "Run mode not recognized!", &
                                "Please choose a valid option"
                            WRITE(output_unit,'(A)') (TRIM(usage(j)),j=1,n_usage)
                            8005 FORMAT (A,/,A,/,A)
                            STOP
                        END IF
                    END IF
                ELSE IF (TMP_ARG .EQ. "-h" .OR. TMP_ARG .EQ. "--help") THEN
                    WRITE(output_unit,'(A)') (TRIM(prg_descrip(j)),j=1,n_prg_descrip)
                    WRITE(output_unit,'(A)') (TRIM(usage(j)),j=1,n_usage)
                    STOP
                ELSE
                    WRITE(output_unit,8006) "ERROR", &
                        "Command-line argument not recognized!", &
                        "Offending argument:",TRIM(TMP_ARG)
                    WRITE(output_unit,'(A)') (TRIM(usage(j)),j=1,n_usage)
                    8006 FORMAT (A,/,A,/,A,2X,A)
                    STOP
                END IF
            END IF
        END DO
    END IF
    
    IF (.NOT. infile_check) THEN
        WRITE(output_unit,8007) "ERROR", &
            "No -in key and no input filename provided!", &
            "Check that the proper arguments are being supplied as '-key' 'input'"
        WRITE(output_unit,'(A)') (TRIM(usage(j)),j=1,n_usage)
        8007 FORMAT (A,/,A,/,A)
        STOP
    ELSE IF (.NOT. runmode_check) THEN
        WRITE(output_unit,8008) "ERROR", &
            "No run mode key or input arguments provided!", &
            "Check that the proper arguments are being supplied as '-key' 'input'"
        WRITE(output_unit,'(A)') (TRIM(usage(j)),j=1,n_usage)
        8008 FORMAT (A,/,A,/,A)
        STOP
    END IF
    
    
    
    ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
    !
    ! Read parameters from the input control file
    !
    ! TODO
    ! - Move whole section to subroutine?
    ! - Add in ability to utilize multiple heads files
    ! - Add in a read of which stress period and time step to use for heads
    !
    ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
    
    WRITE (output_unit,'(A)',advance='no') "Reading Input Control File . . ."
    
    OPEN(NEWUNIT=fin, FILE=control_file, FORM='FORMATTED', STATUS='OLD', IOSTAT=ioerr &
         , ACTION='read', POSITION='rewind',ACCESS='sequential')
    IF (ioerr .NE. 0) THEN
        WRITE(output_unit,9001) "ERROR",ioerr,"Problem opening",ADJUSTL(TRIM(control_file))
        9001 FORMAT (A,1X,I0,/,A,1X,A)
        STOP
    END IF
    
    ! Initialize the input file line count
    filelinecnt = 0

    ! Read through control file
    cntrloop: DO
        ! Read the whole line at once -- one giant string
        READ(fin,'(A)', iostat=ioerr) line
        IF (ioerr .GT. 0) THEN
            WRITE(output_unit,9002) "ERROR", ioerr, &
                                    "Problem reading the input file line:", TRIM(line) &
                                    , "File:", ADJUSTL(TRIM(control_file)), "Line number:", (filelinecnt+1)
            9002 FORMAT (A,1X,I0,/,A,1X,A,/,A,1X,A,1X,A,2X,I0)
            STOP
        ELSE IF (ioerr .EQ. iostat_end) THEN
            ! End of File...Exit the loop
            EXIT cntrloop
        ELSE
            ! Increment the input file line count
            filelinecnt = filelinecnt + 1
            
            ! Place contents of the line into the line_cols array
            lineread: DO line_index=1,max_number_of_columns,1
                READ(line,*,iostat=ioerr) line_cols(1:line_index)
                IF (ioerr==-1) EXIT lineread
            END DO lineread
        END IF
        
!             ELSE IF (TRIM(line_cols(1)) .EQ. "set" .AND TRIM(line_cols(2)) .EQ. "Number_Of_Lake_Waterbody_Files:") THEN
!                 CALL str2int32(ADJUSTL(TRIM(input_header_value)), n_waterbodies_files, ioerr)
!                 if (ioerr .NE. 0) then
!                     write(*,'(A,I0,A,A)') "ERROR ", ioerr, &
!                                             ": Problem converting string to integer: ", &
!                                             input_header_value
!                     stop
!                 else
!                     ! Allocate the number of lake files to use
!                     ALLOCATE ( waterbodies_infile( n_waterbodies_files ) )
!                     ALLOCATE ( waterbodies_outfile_prefix( n_waterbodies_files ) )
!                 end if
        
        IF (TRIM(line_cols(1)) .EQ. "set" .AND. TRIM(line_cols(2)) .EQ. "Number_Heads_Files") THEN
            
            ! Increment the input file line count
            !filelinecnt = filelinecnt + 1 ! Already counted
            
            ! Convert the number of files from a string to an integer
            READ (line_cols(3),*) n_hds_files
            
            ! Allocate arrays with the count of heads files
            ALLOCATE ( hds_file_id( n_hds_files ) )
            ALLOCATE ( hds_file_list( n_hds_files ) )
            
            
            ! Read through list of heads files
            i = 0
            rheadsf: DO WHILE (i<n_hds_files)
                READ(fin,'(A)', iostat=ioerr) line
                IF (ioerr .GT. 0) THEN
                    WRITE(output_unit,9003) "ERROR", ioerr, &
                                            "Problem reading the input file line:", TRIM(line) &
                                            , "File:", ADJUSTL(TRIM(control_file)), "Line number:", (filelinecnt+1)
                    9003 FORMAT (A,1X,I0,/,A,1X,A,/,A,1X,A,1X,A,2X,I0)
                    STOP
                ELSE IF (ioerr .EQ. iostat_end) THEN
                    ! End of File...Not supposed to happen before the end of the list
                    WRITE(output_unit,9004) "ERROR", ioerr, &
                                            "Reached EOF while reading Heads file list. Check input file.", &
                                            "File:", ADJUSTL(TRIM(control_file)), "Line number:", (filelinecnt+1)
                    9004 FORMAT (A,1X,I0,/,A,/,A,1X,A,2X,A,1X,I0)
                    STOP
                ELSE
                    ! Increment the input file line count
                    filelinecnt = filelinecnt + 1
                    
                    ! Place contents of the line into the line_cols array
                    lineread3: DO line_index=1,max_number_of_columns,1
                        READ(line,*,iostat=ioerr) line_cols(1:line_index)
                        IF (ioerr==-1) EXIT lineread3
                    END DO lineread3
                
                    IF (TRIM(line_cols(1)) .EQ. "set" .AND. TRIM(line_cols(2)) .EQ. "HeadsFile") THEN
                        ! Increment counters
                        i = i + 1
                        
                        ! Set the value of the filenames
                        hds_file_id(i) = ADJUSTL(TRIM(line_cols(3)))
                        !hds_file_id = ADJUSTL(TRIM(line_cols(2)))
                        hds_file_list(i) = ADJUSTL(TRIM(line_cols(4)))
                        !hds_file = ADJUSTL(TRIM(line_cols(3)))
                        !print*, TRIM(line_cols(3)), " ", TRIM(line_cols(4))
                    ENDIF
                END IF
            END DO rheadsf
            !print*, hds_file_id_length, n_hds_files, filelinecnt
            !print*, ADJUSTL(TRIM(hds_file_id(1))), TRIM(hds_file_list(1))
            
        ELSE IF (TRIM(line_cols(1)) .EQ. "set" .AND. TRIM(line_cols(2)) .EQ. "Delta_Heads_Prefix") THEN
            
            ! Increment the input file line count
            !filelinecnt = filelinecnt + 1 ! Already counted
            
            ! Read in the name of the prefix for the delta heads output files
            deltaH_filename_prefix = ADJUSTL(TRIM(line_cols(3)))
            
        ELSE IF (TRIM(line_cols(1)) .EQ. "begin" .AND. TRIM(line_cols(2)) .EQ. "Waterbody_InputFile_OutputPrefix") THEN
            
            ! Initialize the count of Waterbody files
            n_waterbodies_files = 0
            
            ! Initialize the section counter
            sectioncnt = 0
            
            ! First read through to count the number of Waterbody files
            rwbf1: DO
                READ(fin,'(A)', iostat=ioerr) line
                
                IF (ioerr .GT. 0) THEN
                    WRITE(output_unit,9005) "ERROR", ioerr, &
                                            "Problem reading the input file line:", TRIM(line) &
                                            , "File:", ADJUSTL(TRIM(control_file)), "Line number:", (filelinecnt+1)
                    9005 FORMAT (A,1X,I0,/,A,1X,A,/,A,1X,A,1X,A,2X,I0)
                    STOP
                ELSE IF (ioerr .EQ. iostat_end) THEN
                    ! End of File...Not supposed to happen until after the "end" keyword
                    WRITE(output_unit,9006) "ERROR ", ioerr, &
                                            "Reached EOF while reading Lake Waterbody List.", &
                                            "Required section 'end' statement not found.", &
                                            "File:", ADJUSTL(TRIM(control_file)), "Line number:", (filelinecnt+1)
                    9006 FORMAT (A,1X,I0,/,A,/,A,/,A,1X,A,2X,A,1X,I0)
                    STOP
                ELSE
                    ! Increment the input file line count
                    filelinecnt = filelinecnt + 1
                    
                    ! Place contents of the line into the line_cols array
                    lineread4: DO line_index=1,max_number_of_columns,1
                        READ(line,*,iostat=ioerr) line_cols(1:line_index)
                        IF (ioerr==-1) EXIT lineread4
                    END DO lineread4
                
                    IF (TRIM(line_cols(1)) .EQ. "fileset") THEN
                        ! Increment counters
                        sectioncnt = sectioncnt + 1
                        n_waterbodies_files = n_waterbodies_files + 1
                    ELSE IF (TRIM(line_cols(1)) .EQ. "end" .AND. &
                                TRIM(line_cols(2)) .EQ. "Waterbody_InputFile_OutputPrefix") THEN
                        ! Only increment the section counter
                        sectioncnt = sectioncnt + 1
                        
                        ! End of the list encountered...get out of the loop
                        EXIT rwbf1
                    ELSE ! Other characters or blank line encountered
                        ! Only increment the section counter
                        sectioncnt = sectioncnt + 1
                    ENDIF
                END IF
            END DO rwbf1
            
            
            ! Allocate arrays with the count of Waterbody files and rewind the file
            ALLOCATE ( waterbodies_infile( n_waterbodies_files ) )
            ALLOCATE ( waterbodies_outfile_prefix( n_waterbodies_files ) )
            DO i=1, sectioncnt
                BACKSPACE (fin)
            END DO
            filelinecnt = filelinecnt - sectioncnt
            
            
            ! Re-initialize the section counter
            sectioncnt = 0
            
            
            ! Read through a second time to actually read the information
            rwbf2: DO
                READ(fin,'(A)', iostat=ioerr) line
                IF (ioerr .GT. 0) THEN
                    WRITE(output_unit,9007) "ERROR", ioerr, &
                                            "Problem reading the input file line:", TRIM(line) &
                                            , "File:", ADJUSTL(TRIM(control_file)), "Line number:", (filelinecnt+1)
                    9007 FORMAT (A,1X,I0,/,A,1X,A,/,A,1X,A,1X,A,2X,I0)
                    STOP
                ELSE IF (ioerr .EQ. iostat_end) THEN
                    ! End of File...Not supposed to happen until after the "end" keyword
                    WRITE(output_unit,9008) "ERROR ", ioerr, &
                                            "Reached EOF while reading Lake Waterbody List.", &
                                            "Required section 'end' statement not found.", &
                                            "File:", ADJUSTL(TRIM(control_file)), "Line number:", (filelinecnt+1)
                    9008 FORMAT (A,1X,I0,/,A,/,A,/,A,1X,A,2X,A,1X,I0)
                    STOP
                ELSE
                    ! Increment the input file line count
                    filelinecnt = filelinecnt + 1
                    
                    ! Place contents of the line into the line_cols array
                    lineread5: DO line_index=1,max_number_of_columns,1
                        READ(line,*,iostat=ioerr) line_cols(1:line_index)
                        IF (ioerr==-1) EXIT lineread5
                    END DO lineread5
                
                    IF (TRIM(line_cols(1)) .EQ. "fileset") THEN
                        ! Increment counters
                        sectioncnt = sectioncnt + 1
                        
                        ! Set the value of the filenames
                        waterbodies_infile(sectioncnt) = ADJUSTL(TRIM(line_cols(2)))
                        waterbodies_outfile_prefix(sectioncnt) = ADJUSTL(TRIM(line_cols(3)))
                    ELSE IF (TRIM(line_cols(1)) .EQ. "end" .AND. &
                                TRIM(line_cols(2)) .EQ. "Waterbody_InputFile_OutputPrefix") THEN
                        ! Only increment the section counter
                        sectioncnt = sectioncnt + 1
                        
                        ! End of the list encountered...get out of the loop
                        EXIT rwbf2
                    ENDIF
                END IF
            END DO rwbf2
        
        END IF
    END DO cntrloop
    
    CLOSE(fin)
    
    ! Append prefix and suffixes to create the output filename
    deltaH_filename = &
        ADJUSTL(TRIM(deltaH_filename_prefix)) &
        //ADJUSTL(TRIM(layer_suffix))//"AllLayers"//ADJUSTL(TRIM(suffix))
    
    WRITE(output_unit,1000,advance='yes') "COMPLETE" &
          , "Number of Input Control File lines   ",filelinecnt &
          , "Heads filename(s): ",ADJUSTL(TRIM(hds_file_list(1))) &
          , "dH filename(s): ",ADJUSTL(TRIM(deltaH_filename)) &
          , "Number of Waterbody (WB) input files and output prefixes: ",n_waterbodies_files
    DO i=1,n_waterbodies_files,1
        WRITE(output_unit,1001) "WB_",TRIM(itoa(i)) &
            ,ADJUSTL(TRIM(waterbodies_infile(i))) &
            ,ADJUSTL(TRIM(waterbodies_outfile_prefix(i)))
    END DO
    WRITE(output_unit,'(/)')
    1000 FORMAT (3X,A,/,/,A,I0,/,2A,/,2A,/,A,I0)
    1001 FORMAT (2A,1X,A,1X,A)
    ! ooooooooooooooooooooooooooooooooooooooooooooooooooooo
    
    
    
    IF (runmode .EQ. 'run') THEN
        
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        !
        ! READ EACH SIMULATED HEADS FILE
        !
        ! TODO
        ! - Add in ability to utilize multiple heads files
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        ! Add heads filename value
        hds_file = ADJUSTL(TRIM(hds_file_list(1)))
        
        WRITE (output_unit,'(A,/)',advance='yes') "Reading heads . . ."
        CALL read_modflow_heads(hds_file, hds_filename_length, hds, kper, kstp, nlay, ncol, nrow)
        WRITE (output_unit,'(3X,A,/)',advance='yes') ". . . COMPLETE"
        ! ooooooooooooooooooooooooooooooooooooooooooooooooooooo
        
        
        
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        !
        ! CALCULATE THE HEAD DIFFERENCE FOR EACH MODEL CELL
        !
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        WRITE (output_unit,'(A)',advance='no') "Calculating delta H . . ."
        CALL delta_head_modelwide(nlay, nrow, ncol, per_b, stp_b, per_a, stp_a, deltaH_filename, hds)
        WRITE (output_unit,'(3X,A,/)',advance='yes') "COMPLETE"
        ! ooooooooooooooooooooooooooooooooooooooooooooooooooooo
        
        
        
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        !
        !	EXTRACT AND EVALUATE AREA-AVERAGED LAKE HEADS
        !
        ! xoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxoxox
        WRITE (output_unit,'(A,/)') "Calculate area-averaged lake heads and differences . . ."
        ! Extract lake heads for each lake area input file
        DO cur_waterbodies_file = 1, n_waterbodies_files
            CALL avg_lakehead_n_diff(kstp, kper, nlay, per_b, stp_b, per_a, stp_a &
                                    , TRIM(waterbodies_infile(cur_waterbodies_file)) &
                                    , ADJUSTL(TRIM(waterbodies_outfile_prefix(cur_waterbodies_file))) &
                                    , hds)
        END DO
        WRITE (output_unit,'(3X,A,/,/,A,/)') ". . . COMPLETE","DONE PROCESSING HEADS FILE"
            
    END IF
END PROGRAM MAIN
