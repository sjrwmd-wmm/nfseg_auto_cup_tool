# Python program to read a MODFLOW float array, adjusting values
# using data read in from a table, and write the new array.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Please report errors and corrections to jwg (at) srwmd.org

#
# 2013-06-05    jwg   original code (adjustFloatArrayValues.py)
# 2013-08-06    jwg   add methods to extract values from array and write to a table
#                     (new program name, extractFloatArrayValues.py)
# 2013-08-06    jwg   add method to write all elements of the array as a csv table
# 2014-09-02    jwg   add arrays indicating no-flow and dry-cell status


import os
import math
import shelve
import numpy as np

class ModelGrid:
    def __init__(self,gridTuple):
        self.layers, self.rows, self.columns = gridTuple
        self.gridTuple = gridTuple

class MFFloatArray:
    """ Class representing a two-dimensional MODFLOW float data array. """
    def __init__(self, myGrid, arrayInputFileName, valuesPerLine, fieldWidth, fieldFormat, head_noflow, head_dry):
        self.grid = myGrid
        self.inFile = open(arrayInputFileName, 'r')
        self.valuesPerLine = valuesPerLine
        self.fieldWidth = fieldWidth
        self.fieldFormat = fieldFormat
        self.head_noflow = head_noflow
        self.head_dry = head_dry
        self.calcDataBlockProperties()
        self.initialize_arrays()

    def initialize_arrays(self):
        self.np_array = np.empty((self.grid.rows, self.grid.columns), dtype=float)
        self.dry_cell = np.empty((self.grid.rows, self.grid.columns), dtype=bool)
        self.dry_cell[:, :] = False
        self.noflow_cell = np.empty((self.grid.rows, self.grid.columns), dtype=bool)
        self.noflow_cell[:, :] = False
        self.list_array = []

    def calcDataBlockProperties(self):
        if self.grid.columns % self.valuesPerLine == 0:
            self.linesPerBlock = int(math.floor(self.grid.columns/self.valuesPerLine))
            self.blockType = "filled"
            self.valuesInLastLineOfBlock = 0
        else:
            self.linesPerBlock = int(math.floor(self.grid.columns/self.valuesPerLine)) + 1
            self.blockType = "unFilled"
            self.valuesInLastLineOfBlock = self.grid.columns - (self.linesPerBlock - 1)*self.valuesPerLine
           
    def parseFloatArray(self):
        for i in range(0,self.grid.rows):
            thisRow = i + 1
            thisCol = 0
            self.block_list = []
            self.parseBlock(thisRow, thisCol)
            self.list_array.append(self.block_list)

    def parseBlock(self, thisRow, thisCol):
        for i in range(0, self.linesPerBlock):
            if i == self.linesPerBlock - 1:
                valuesToRead = self.valuesInLastLineOfBlock
            else:
                valuesToRead = self.valuesPerLine
            thisCol = self.parseLine(thisRow, thisCol, valuesToRead)

    def parseLine(self, thisRow, thisCol, valuesToRead):
        line = self.inFile.readline()
        for i in range(0, valuesToRead):        
            thisCol += 1
            startIndex = i*self.fieldWidth
            endIndex = startIndex + self.fieldWidth
            thisValue = float(line.rstrip()[startIndex:endIndex])
            self.np_array[thisRow-1][thisCol-1] = thisValue
            self.block_list.append(thisValue)
            self.check_for_dry_or_no_flow(thisRow, thisCol, thisValue)
        return(thisCol)
    
    def check_for_dry_or_no_flow(self, thisRow, thisCol, thisValue):
        if abs(thisValue - self.head_noflow) < 1.:
            self.noflow_cell[thisRow-1][thisCol-1] = True        
        if abs(thisValue - self.head_dry) < 1.:
            self.dry_cell[thisRow-1][thisCol-1] = True
    
    # This function might be deprecated !!! PMB !!! 20200601
#    def extractCellValue(self, cellAddress):
#        layer, row, col = cellAddress
#        if self.is_this_a_valid_cell_address(cellAddress) == True:
#            outValue = self.np_array[row-1][col-1]
#        return(outValue)
    
    # This function might be deprecated !!! PMB !!! 20200601
#    def is_this_a_valid_cell_address(self, cellAddress):
#        if row < 0 or row > self.np_array.shape[0]:
#            raise ValueError, 'row = %i does not occur in the array' % (row)
#        elif self.np_array < 0 or col > self.np_array.shape[1]:
#            raise ValueError, 'col = %i does not occur in the array' % (col)
#        else:
#            return True
    
    # This function might be deprecated !!! PMB !!! 20200601
#    def writeArray(self):
#        outFile = raw_input("Please enter name of output file: ")
#        with open(outFile, 'w') as self.outFile:
#            for i in range(0,self.grid.rows):
#                thisRow = i + 1
#                thisCol = 0
#                self.writeDataBlock(thisRow, thisCol)
#        #
    
    # This function might be deprecated !!! PMB !!! 20200601
#    def writeDataBlock(self, thisRow, thisCol):
#        for i in range(0, self.linesPerBlock):
#            if i == self.linesPerBlock - 1:
#                valuesToWrite = self.valuesInLastLineOfBlock
#            else:
#                valuesToWrite = self.valuesPerLine
#            thisCol = self.writeLine(thisRow, thisCol, valuesToWrite)
    
    # This function might be deprecated !!! PMB !!! 20200601
#    def writeLine(self, thisRow, thisCol, valuesToWrite):
#        line = ''
#        for i in range(0, valuesToWrite):        
#            thisCol += 1
#            stringToAppend = self.fieldFormat % (self.np_array[thisRow-1][thisCol-1])
#            line = line + stringToAppend
#        self.outFile.write(line + '\n')
#        return(thisCol)
    
    # This function might be deprecated !!! PMB !!! 20200601
#    def writeAndAdjustAnArray(self, tableDict, layerToAdjust):
#        """ Write a MODFLOW array to an ascii output file. Adjust values if they have
#            a corresponding cell address in a dictionary of 'table values'.
#        """
#        self.adjustedValuesDict = tableDict
#        self.layerToAdjust = layerToAdjust
#        for i in range(0,self.grid.rows):
#            thisRow = i + 1
#            thisCol = 0
#            self.writeDataBlockAfterAdjustingValue(thisRow, thisCol)
    
    # This function might be deprecated !!! PMB !!! 20200601
#    def writeDataBlockAfterAdjustingValue(self, thisRow, thisCol):
#        for i in range(0, self.linesPerBlock):
#            if i == self.linesPerBlock - 1:
#                valuesToWrite = self.valuesInLastLineOfBlock
#            else:
#                valuesToWrite = self.valuesPerLine
#            thisCol = self.writeLineAfterAdjustingValue(thisRow, thisCol, valuesToWrite)
    
    # This function might be deprecated !!! PMB !!! 20200601
#    def writeLineAfterAdjustingValue(self, thisRow, thisCol, valuesToWrite):
#        line = ''
#        for i in range(0, valuesToWrite):        
#            thisCol += 1
#            if (thisRow, thisCol, 3) == (2, 1, 3):
#                pass
#            if self.adjustedValuesDict.has_key((thisRow, thisCol, self.layerToAdjust, 'gridCode')):
#                adjustment = -1*self.adjustedValuesDict[(thisRow, thisCol, self.layerToAdjust, 'gridCode')]
#                outputValue = self.np_array[thisRow-1][thisCol-1] + adjustment
#            else:
#                outputValue = self.np_array[thisRow-1][thisCol-1]
#            stringToAppend = self.fieldFormat % (outputValue,)
#            line = line + stringToAppend
#        self.outFile.write(line + '\n')
#        return(thisCol)
    
    def writeFloatArrayAsTable(self, array_layer, results_dir):
        """ Write the data to an ASCII file with two columns: cell sequence number, and cell value. """
        outputFileName = os.path.join(results_dir,"dh_lyr{0}".format(array_layer))
        with open(outputFileName + '_tableFormat.csv', 'w') as outputFile:
            headerString = "{0},dh_lyr{1}\n".format('cellAddress2D',array_layer)
            outputFile.write(headerString)
            for row in range(1, self.grid.rows+1):
                for column in range(1, self.grid.columns+1):
                    seqnum = (row - 1)*self.grid.columns + column
                    value = self.np_array[row-1][column-1]
                    outString = "{0},{1}\n".format(seqnum, value)
                    outputFile.write(outString)
        #

# This function might be deprecated !!! PMB !!! 20200601
#class MFCells:
#    
#    def __init__(self):
#        self.cellList = []
#        inFile = raw_input("Please enter name of file with cell addresses for extracting data from the array: ")
#        self.inFile = open(inFile, 'r')
#
#    def parseInputFile(self):
#        for i in self.inFile.readlines():
#            self.parseLine(i)
#
#    def parseLine(self,line):
#        lineList = line.rstrip().split(',')
#        layer, row, col = tuple([int(i) for i in lineList[0:3]])
#        if len(self.cellList) > 1 and ((layer,row,col) in self.cellList):
#            raise ValueError, 'cell address (%i, %i, %i) occurs elsewhere in the input table' % (layer,row,col)
#        else:
#            self.cellList.append((layer, row, col))

# This function may be deprecated !!! PMB !!! 20200601
#def openFiles():
#    outFileName = raw_input("Please enter name of output file that will contain heads for each cell: ")
#    cellValuesOutputFile = open(outFileName, 'w')        
#    outFileName = raw_input("Please enter name of output file that will contain the minimum head among the selected cells: ")
#    minValueOutputFile = open(outFileName, 'w')
#    return((cellValuesOutputFile,minValueOutputFile))

def read_spec_file(array_spec_in):
    
    with open(array_spec_in, 'r') as f: lines = f.readlines()
    
    grid_dims = lines[0].rstrip().split(',')
    layers, rows, columns = tuple([int(x) for x in grid_dims])
    valuesPerLine, fieldWidth, fieldFormat = tuple(lines[1].rstrip().split(','))
    valuesPerLine, fieldWidth = tuple([int(x) for x in [valuesPerLine, fieldWidth]])
    head_indications = lines[2].rstrip().split(',')
    head_noflow, head_dry = tuple([float(x) for x in head_indications])
    
    return (layers, rows, columns,
            valuesPerLine, fieldWidth,
            fieldFormat, head_noflow, head_dry)

# This function is being depricated
# !!! PMB !!! 20200601
#def read_array_file_names(array_file_names_in):
#    """ Read a file listing model layer number and corresponding name of head output file.
#    
#        This function expects the file name to be 'sim_head_arrays_file_names.asc'. The
#        file should be comma-delimited, ASCII-formatted, and have two fields in each
#        record: integer layer number, followed by the name of the file containing the
#        simulated heads.
#    """
#    array_names = []
#    
#    with open(array_file_names_in, 'r') as f:
#        for line in f.readlines():  # Should thhis be readlines or readline? !!! PMB
#            array_data = tuple(line.rstrip().split(','))
#            array_names.append(array_data)
#    #
#    return array_names

def read_arrays(array_spec_in, array_file_names_in, results_dir, logfile):
#def main():
    # These values may not be used !!! PMB !!! 20200601
    #minValue = 1.2345e25  # !!! PMB !!! What is this?
    #minValueCell = (0,0,0)
    
    (layers, rows, columns,
     valuesPerLine, fieldWidth,
     fieldFormat, head_noflow, head_dry) = read_spec_file(array_spec_in)
    
    myGrid = ModelGrid((layers, rows, columns))    

    array_dict = {}
    #book = shelve.open('test.shelf')
    # Working to deprecate this function !!! PMB !!! 20200601
    #array_file_name_tuples = read_array_file_names(array_file_names_in)
    """ Read a file listing model layer number and corresponding name of head output file.
    
        This function expects the file name to be 'sim_head_arrays_file_names.asc'. The
        file should be comma-delimited, ASCII-formatted, and have two fields in each
        record: integer layer number, followed by the name of the file containing the
        simulated heads.
    """
    with open(array_file_names_in, 'r') as f:
        for line in f:
            array_layer, array_file_name = line.rstrip().split(',')
            
            currentmessage = ('\tprocessing array %s\n' % (array_file_name))
            print (currentmessage)
            with open(logfile,'a') as lf: lf.write(currentmessage)
            
            anArray = MFFloatArray(myGrid, array_file_name, valuesPerLine,
                                   fieldWidth, fieldFormat, head_noflow,
                                   head_dry)
            anArray.parseFloatArray()
            anArray.writeFloatArrayAsTable(array_layer,results_dir)
            #book[array_layer] = anArray.np_array
            array_dict[(array_layer, 'values')] = anArray.np_array
            array_dict[(array_layer, 'dry')] = anArray.dry_cell
            array_dict[(array_layer, 'no_flow')] = anArray.noflow_cell
    
#    for array_file_name_tuple in array_file_name_tuples:
#        array_layer, array_file_name = array_file_name_tuple
#        print('    processing array %s' % (array_file_name))
#        anArray = MFFloatArray(myGrid, array_file_name, valuesPerLine, fieldWidth, fieldFormat, head_noflow, head_dry)
#        anArray.parseFloatArray()
#        anArray.writeFloatArrayAsTable(array_layer)
#        #book[array_layer] = anArray.np_array
#        array_dict[(array_layer, 'values')] = anArray.np_array
#        array_dict[(array_layer, 'dry')] = anArray.dry_cell
#        array_dict[(array_layer, 'no_flow')] = anArray.noflow_cell
    ##book.close()
    currentmessage = ('\tFinished reading arrays\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    return array_dict

def main(results_dir, array_spec_in, array_file_names_in, logfile): # !!! PMB !!! Search out the input filenames throughout
    """ read a set of modflow arrays, and output values to a set of corresponding
        comma-delimited tables with two columns (MODFLOW cell address, cell value).
    """
    
    # TODO: Create a master control file tailored to the model
    #       It should list the pertenent input values
    
    # Files come from input_and_definition_files/postproc/dh
    #----------------------------------
    #array_spec_in = 'array_reader.spc'
    #array_file_names_in = 'sim_head_arrays_file_names.asc'
    #----------------------------------
    
    array_dict = read_arrays(array_spec_in,array_file_names_in, results_dir, logfile)
    
    currentmessage = ('\tModflow array processing complete\n')
    print (currentmessage)
    with open(logfile,'a') as lf: lf.write(currentmessage)
    
    
    return

#main()
