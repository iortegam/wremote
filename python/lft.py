#!/usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        lft.py
#
# Purpose:
#         - Run Linefit
#         - Plot Results
#         - Calculate post-processing and improvements in lft inputs 
# Notes:
#         - input_lft.py must be provided (see usage)
#         - Noe: for now OPUS Files with TRANSMISSION block must be provided
#
# Usage:
#     lft.py
#
# Version History:
#       Created, July, 2018  Ivan Ortega (iortega@ucar.edu)
#
#----------------------------------------------------------------------------------------


                        #-------------------------#
                        # Import Standard modules #
                        #-------------------------#
import sys
import os
from os import walk
import getopt
import subprocess as sp
import shutil
import logging
import datetime as dt
import numpy as np

import matplotlib.dates as md
import matplotlib.dates as md
from matplotlib.dates import DateFormatter, MonthLocator, YearLocator, DayLocator, WeekdayLocator, MONDAY

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import FormatStrFormatter, MultipleLocator,AutoMinorLocator,ScalarFormatter
from matplotlib.backends.backend_pdf import PdfPages #to save multiple pages in 1 pdf...
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.cm as mplcm
import matplotlib.colors as colors
import matplotlib.gridspec as gridspec

import classlft
import subprocess
from   time           import sleep


def usage():
    ''' Prints to screen standard program usage'''
    print ('lft.py -i input_lft.py')

        
def ckDir(dirName,logFlg=False,exit=False):
    ''' '''
    if not os.path.exists( dirName ):
        print ('Input Directory %s does not exist' % (dirName))
        if logFlg: logFlg.error('Directory %s does not exist' % dirName)
        if exit: sys.exit()
        return False
    else:
        return True   

def ckDirMk(dirName,logFlg=False):
    ''' '''
    if not ( os.path.exists(dirName) ):
        os.makedirs( dirName )
        if logFlg: logFlg.info( 'Created folder %s' % dirName)  
        return False
    else:
        return True
        
def ckFile(fName,logFlg=False,exit=False):
    '''Check if a file exists'''
    if not os.path.isfile(fName):
        print ('File %s does not exist' % (fName))
        if logFlg: logFlg.error('Unable to find file: %s' % fName)
        if exit: sys.exit()
        return False
    else:
        return True

def subProcRun( fname, logFlg=False ):
    '''This runs a system command and directs the stdout and stderr'''
    #rtn = subprocess.Popen( fname, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    rtn = subprocess.Popen( fname, stderr=subprocess.PIPE )
    outstr = ''
    for line in iter(rtn.stderr.readline, b''):
        print (line.rstrip())
        if logFlg: outstr += line

    if logFlg: logFlg.info(outstr)

    return True



                            #----------------------------#
                            #                            #
                            #        --- Main---         #
                            #                            #
                            #----------------------------#

def main(argv):

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:?')

    except getopt.GetoptError as err:
        print (str(err))
        usage()
        sys.exit()

    #-----------------------------
    # Parse command line arguments
    #-----------------------------
    for opt, arg in opts:

        if opt == '-i':

            pltInputs = {}

            ckFile(arg,exit=True)

            try:
                #execfile(arg, pltInputs)
                exec(compile(open(arg, "rb").read(), arg, 'exec'), pltInputs)
            except IOError as errmsg:
                print (errmsg + ' : ' + arg)
                sys.exit()

            if '__builtins__' in pltInputs:
                del pltInputs['__builtins__']               

        elif opt == '-?':
            usage()
            sys.exit()

        else:
            print ('Unhandled option: ' + opt)
            sys.exit()


    #---------------------------------#
    # Check / in directories
    #---------------------------------#
    if not( pltInputs['pathDir'].endswith('/') ):
        pltInputs['pathDir'] = pltInputs['pathDir'] + '/'

    if not( pltInputs['spcDir'].endswith('/') ):
        pltInputs['spcDir'] = pltInputs['spcDir'] + '/'

    #---------------------------------#
    # Check directories and Files
    #---------------------------------#
    ckDir(pltInputs['pathDir'])
    ckDir(pltInputs['spcDir'])

    if pltInputs['lftFlg']:
    
        ckFile(pltInputs['DefaultInp'])
        ckFile(pltInputs['lfit'])
        ckFile(pltInputs['spcDir'] + pltInputs['spc'])
    
        ckDirMk(pltInputs['pathDir'] + 'ergs')
            
        #---------------------------------#
        # Copying spc to base directory; if a path is input in linefit an error arise
        #---------------------------------#
        if pltInputs['spcDir'] != pltInputs['pathDir']:
            shutil.copy (pltInputs['spcDir'] + pltInputs['spc'], pltInputs['pathDir'] + pltInputs['spc'])

        #---------------------------------#
        # Read Default Parameters
        #---------------------------------#
        with open(pltInputs['DefaultInp'] ,'r') as fopen: lines = fopen.readlines()

        #---------------------------------#
        # Number of mw
        #---------------------------------#
        ind1       = [ind for ind,line in enumerate(lines) if 'number of microwindows' in line][0]
        ind2       = [ind for ind,line in enumerate(lines[ind1:]) if '$' in line][0]
        indP       = ind1 + ind2 + 1
        Numws      = int(lines[indP].strip().split(',')[0])

        #---------------------------------#
        # Format of spc
        #---------------------------------#
        ind1       = [ind for ind,line in enumerate(lines) if 'format of spectra' in line][0]
        ind2       = [ind for ind,line in enumerate(lines[ind1:]) if '$' in line][0]
        indP       = ind1 + ind2 + 1
        formatspc = int(lines[indP].strip().split(',')[0])

        if formatspc != 2:
            print ("Error: Format of spectra must be transmission!")
            exit()

        #---------------------------------#
        # Input the spectra of interest in all mw
        #---------------------------------#
        for i in range(int(Numws)):
            lines[indP + i+ 1] = pltInputs['spc']+'\n' 

        #---------------------------------#
        # if True Re-sampling
        #---------------------------------#
        if pltInputs['ResampFlg']:
            
            ind1       = [ind for ind,line in enumerate(lines) if 'Resampling' in line][0]
            ind2       = [ind for ind,line in enumerate(lines[ind1:]) if '$' in line][0]
            indP       = ind1 + ind2 + 1

            lines[indP]   = '.true.\n'
            lines[indP+1] = str(pltInputs['Resamp'])+'\n'

        #---------------------------------#
        # max OPD and apt/foclength;  #aperture radius / focal length of collimator
        #---------------------------------#
        ind1       = [ind for ind,line in enumerate(lines) if 'instrumental parameters' in line][0]
        ind2       = [ind for ind,line in enumerate(lines[ind1:]) if '$' in line][0]
        indP       = ind1 + ind2 + 1

        lines[indP+1]   = str(pltInputs['maxopd'])+'\n'
        lines[indP+3]   = str('{:.6f}'.format(float(pltInputs['aperture'])/float(pltInputs['foclength']) /2.))+'\n' 
        
        #---------------------------------#
        # Read initial column, temp, pressure
        #---------------------------------#
        ind1       = [ind for ind,line in enumerate(lines) if 'species parameters:' in line][0]
        ind2       = [ind for ind,line in enumerate(lines[ind1:]) if '$' in line][0]
        indP       = ind1 + ind2 + 1

        iTemp = float(lines[indP].strip().split(',')[0])
        iCol  = float(lines[indP].strip().split(',')[2])
        iPres = float(lines[indP].strip().split(',')[3])

        print ('\n******* Initial Input Parameters in defaults lft1.input **********')
        print ('Column [molec/cm2]    = {}'.format(iCol))
        print ('Temperature [Kelvin]  = {}'.format(iTemp))
        print ('Pressure [mbar]       = {}'.format(iPres))
        print ('********************************************************************')

        #---------------------------------#
        # Create the input file for linefit
        #---------------------------------#
        with open(pltInputs['pathDir'] + 'lft14.inp','w') as fout: 
            for line in lines:
                fout.write(line)
        fout.close()
        
        
                                                    #---------------------------------#
                                                    # Retrieve command line arguments #
                                                    #---------------------------------#  

        os.chdir(pltInputs['pathDir'])                                          
        
        ckDir(pltInputs['lfit'], exit=True)
       
        while True:

            print ('\n\n')
            print ('*************************************************')
            print ('*************Begin Linefit Retrieval*****************')
            print ('*************************************************')   

            #---------------------------------#
            # Run linefit
            #---------------------------------#
            rtn = subProcRun( [pltInputs['lfit']])  

            #-------------------------
            # Create Instance of Class 
            #-------------------------    

            lft = classlft.ReadOutputLFT(pltInputs['pathDir']+'/ergs')

            #--------------
            # Read linefit Parameters
            #--------------
            lft.Readactparms()
            lft.Readspecrec()

            print ('*************************************************')
            print ('         Reading linefit outputs                ')
            print ('*************************************************')

            if lft.parms['tempFlg'] >= 1: print ('\nRetrieved Temperature: {0:.3f} Kelvin\n'.format(lft.parms['temp']))
            if lft.parms['presFlg'] >= 1: print ('\nRetrieved Pressure:    {0:.3f} mbar\n'.format(lft.parms['pres']))
            if lft.parms['colFlg'] >= 1:
                for i, c in enumerate(lft.parms['colFactor']):
                    print ('Retrieved Column Factor in Window {0:}: {1:.3f}'.format(i, c))

            tempMean = np.mean(lft.parms['temp'])
            
            #---------------------------------#
            # Read column; after first iteration is updated in the input file
            #---------------------------------#
            
            with open(pltInputs['pathDir'] + 'lft14.inp','r') as fopen: lines = fopen.readlines()
            
            ind1       = [ind for ind,line in enumerate(lines) if 'species parameters:' in line][0]
            ind2       = [ind for ind,line in enumerate(lines[ind1:]) if '$' in line][0]
            indP       = ind1 + ind2 + 1
            
            fopen.close()

            fCol       = float(lines[indP].strip().split(',')[2])
            
            #---------------------------------#
            # Pressure Calculation
            # From lft14.inp: cell column = 7.243e24 * p[mbar] * l[m] / T[K]
            #---------------------------------#

            diffPress    = []
            pressure     = []
            column       = []
            rmse         = []
            colFactor    = []
            
            for i, c in enumerate(lft.parms['colFactor']):
                fPres = (fCol * c * lft.parms['temp'] )/ (pltInputs['cellLength']/100.*7.243e24) 
                pressure.append(fPres)
                rmse.append(lft.spc['rmsePerc_'+str(i)])
                colFactor.append(c)

                print ('\nFinal Column in Window {0:}: {1:.6e} [molec/cm2]'.format(i, fCol * c ))
                column.append(float(fCol * c))

                print ('Final Pressure in Window {0:}: {1:.6f} [mbar]'.format(i, fPres))

                DiffP = iPres - fPres
                print ('Difference of Pressure in Window {0:}: {1:.6f} [mbar], {2:.2f} [%]'.format(i, DiffP, DiffP/fPres * 100.))
              
                diffPress.append(float(DiffP/fPres * 100.)) 
                
                print ('rmse [%] in Window {0:}: {1:.3e}'.format(i, float(lft.spc['rmsePerc_'+str(i)])))

            diffPress    = np.asarray(diffPress)
            pressure     = np.asarray(pressure)
            column       = np.asarray(column)
            rmse         = np.asarray(rmse)
            colFactor    = np.asarray(colFactor)

            columnMean       = np.mean(column)
            pressureMean     = np.mean(pressure)
            diffPressMean    = np.mean(diffPress)
            rmseMean         = np.mean(rmse)
            colFactorMean    = np.mean(colFactor)

            print ('\n********************* Summary of lft results ************************')
            print ('Mean Difference wrt to pressure is: {:.3f} %'.format(diffPressMean))
            print ('Mean rmse [%] is                     : {:.3e}'.format(rmseMean))
            print ('Mean pression is                     : {:.5f}'.format(pressureMean))
            print ('Mean colFactorMean is                : {:.3e}'.format(colFactorMean))
            print ('Mean colFactorMean in % is           : {:.3e}'.format(np.abs(1. -colFactorMean)*100))
            print ('Mean Column is                       : {:.6e}'.format(columnMean))
            print ('\n********************* Summary of lft results ************************')
            

            #---------------------------------#
            # User defines what to do next
            #---------------------------------#
            user_input = input('\nPaused processing....\n Enter: 0 to exit, 1 to update and repeat, 2 show plot retrieval results, 3 save plot retrievals in pdf\n >>> ')
            
            try:
                user_input = int(user_input)
                if not any(user_input == val for val in [0,1,2,3]): raise ValueError
            except ValueError: print ('Please enter 0, 1, 2, or 3')

            if   user_input == 0: 

                if pltInputs['spcDir'] != pltInputs['pathDir']:
                    os.remove(pltInputs['pathDir'] + pltInputs['spc']) 
                
                sys.exit()           # Exit program
            
            elif user_input == 1:                        
                
                with open(pltInputs['pathDir'] + 'lft14.inp','r') as fopen: lines = fopen.readlines()

                ind1       = [ind for ind,line in enumerate(lines) if 'species parameters:' in line][0]
                ind2       = [ind for ind,line in enumerate(lines[ind1:]) if '$' in line][0]
                indP       = ind1 + ind2 + 1

                lines[indP]   = str('{:.3f}, .true., {:.6e}, {:.4f}, .false., {:.4f}, 0.0075'.format(tempMean, columnMean, pressureMean, pressureMean))+'\n'


                with open(pltInputs['pathDir'] + 'lft14.inp','w') as fout: 
                    for line in lines:
                        fout.write(line)


            elif (user_input == 2) or (user_input) == 3:  

                if user_input == 2:
                    saveFlg  = False
                else:
                    saveFlg  = True

                if pltInputs['spcDir'] != pltInputs['pathDir']:
                    os.remove(pltInputs['pathDir'] + pltInputs['spc'])
                    
                if saveFlg: 
                    ckDirMk(pltInputs['pathDir'] + 'results')
                    
                
                pltFile       = pltInputs['pathDir'] + 'results\\lft145_' + pltInputs['spc']+'.pdf'
               
                #-------------------------
                # Create Instance of Class 
                #-------------------------
                lft = classlft.Plotlft(pltInputs['pathDir']+'/ergs', saveFlg=saveFlg, outFname=pltFile)

                #-------------------------
                # Plot Spectra
                #-------------------------
                lft.pltspectra()

                #-------------------------
                # Plot ILS
                #-------------------------
                lft.pltils()

                #-------------------------
                # Plot Modulation/Phase
                #-------------------------
                lft.pltmod()

                #-------------------------
                # Plot cifg
                #-------------------------
                lft.pltcifg()

                #-------------------------
                # Plot Kernel
                #-------------------------
                try:
                    lft.pltkernel()
                except:
                    print ('Unable to plot Kernels: Kernel file Not found?')

                info = ["----------------------------Measurement DATA------------------------\n",
                    "PathDir            = {}\n".format(pltInputs['pathDir'] ),         
                    "PathSpc            = {}\n".format(pltInputs['spcDir'] ) ,             
                    "Spectra            = {}\n".format(pltInputs['spc'] ) , 
                    "Defaults           = {}\n".format(pltInputs['DefaultInp'] ) ,              
                    "-------------------------Instrument Parameters----------------------\n",
                    "maxOPD             = {0:>.3f}\n".format(pltInputs['maxopd'] ) , 
                    "APT                = {0:>.3f}\n".format(pltInputs['aperture'] ) ,
                    "FOC                = {0:>.3f}\n".format(pltInputs['foclength'] ) ,
                    "cellLength         = {0:>.3f}\n".format(pltInputs['cellLength'] ) ,
                    "ResampFlg          = {}\n".format(pltInputs['ResampFlg'] ) ,
                    "Resamp             = {}\n".format(pltInputs['Resamp']),
                    "----------------------------Linefit Retrieval ----------------------\n",
                    "columnMean          = {0:>.6e}\n".format(columnMean ) ,
                    "colFactorMean       = {0:>.5f}\n".format(colFactorMean ) ,                    
                    "tempMean            = {0:>.3f}\n".format(tempMean ) , 
                    "pressureMean        = {0:>.5f}\n".format(pressureMean ),
                    "rmseMean [%]        = {0:>.3f}\n".format(rmseMean ),
                    "diffPress [%]       = {0:>.3f}\n".format(diffPressMean ) ] 

                lft.plttext(info)

                if saveFlg: 
                    lft.closeFig()
                    print ('pdf file saved: {}'.format(pltFile))
                    if ckDir(pltInputs['pathDir'] + 'results\\ergs_'+pltInputs['spc']):
                        #os.remove(pltInputs['pathDir'] + 'ergs_'+pltInputs['spc'])
                        shutil.rmtree(pltInputs['pathDir'] + 'results\\ergs_'+pltInputs['spc'], ignore_errors=True)
                    os.rename(pltInputs['pathDir'] + 'ergs', pltInputs['pathDir'] + 'results\\ergs_'+pltInputs['spc'])
                else:
                    user_input = input('Press any key to exit >>> ')
                
                break

        #---------------------------------#
        # Remove from base
        #---------------------------------#
        
    else:

        print ('*************************************************')
        print ('         Only plotting linefit outputs           ')
        print ('*************************************************')
        
        user_input = raw_input('\nPaused processing....\n Enter: 2 show plot retrieval results, 3 save plot retrievals in pdf\n >>> ')

        try:
            user_input = int(user_input)
            if not any(user_input == val for val in [2,3]): raise ValueError
        except ValueError: print ('Please enter 2, or 3')

        if (user_input == 2) or (user_input) == 3:  

            if user_input == 2:
                saveFlg  = False
            else:
                saveFlg  = True
            
            ckDir(pltInputs['pathDir'] + 'results\\ergs_'+pltInputs['spc'], exit=True)

            pltFile       = pltInputs['pathDir'] + 'results\\lft145_' + pltInputs['spc']+'.pdf'

                #---------------------------------#
                # IF SAVE PDF
                #---------------------------------#
            ckDir(os.path.dirname(os.path.realpath(pltFile)) ,exit=True)

            try:

                #-------------------------
                # Create Instance of Class 
                #-------------------------
                lft = classlft.Plotlft(pltInputs['pathDir'] + 'results\\ergs_'+pltInputs['spc'], saveFlg=saveFlg, outFname=pltFile)

                #-------------------------
                # Plot Spectra
                #-------------------------
                lft.pltspectra()

                #-------------------------
                # Plot ILS
                #-------------------------
                lft.pltils()

                #-------------------------
                # Plot Modulation/Phase
                #-------------------------
                lft.pltmod()

                #-------------------------
                # Plot cifg
                #-------------------------
                lft.pltcifg()

                #-------------------------
                # Plot Kernel
                #-------------------------
                try:
                    lft.pltkernel()
                except:
                    print ('Unable to plot Kernels: Kernel file Not found?')
                
                info = ["----------------------------Measurement DATA------------------------\n",
                    "PathDir            = {}\n".format(pltInputs['pathDir'] ),         
                    "PathSpc            = {}\n".format(pltInputs['spcDir'] ) ,             
                    "Spectra            = {}\n".format(pltInputs['spc'] ) , 
                    "Defaults           = {}\n".format(pltInputs['DefaultInp'] ) ,              
                    "-------------------------Instrument Parameters----------------------\n",
                    "maxOPD             = {0:>.3f}\n".format(pltInputs['maxopd'] ) , 
                    "APT                = {0:>.3f}\n".format(pltInputs['aperture'] ) ,
                    "FOC                = {0:>.3f}\n".format(pltInputs['foclength'] ) ,
                    "cellLength         = {0:>.3f}\n".format(pltInputs['cellLength'] ) ,
                    "ResampFlg          = {}\n".format(pltInputs['ResampFlg'] ) ,
                    "Resamp             = {}\n".format(pltInputs['Resamp']),
                    "----------------------------Linefit Retrieval ----------------------\n",
                    "columnMean          = {0:>.6e}\n".format(columnMean ) ,                   
                    "tempMean            = {0:>.3f}\n".format(tempMean ) , 
                    "pressureMean        = {0:>.3f}\n".format(pressureMean ) ]
                
                lft.plttext(info)

            except:
                print ('Error in Reading previous Linefit Files')


            if saveFlg: 
                lft.closeFig()
                print ('pdf file saved: {}'.format(pltFile))
              
            else:
                user_input = raw_input('Press any key to exit >>> ')
                
            sys.exit()



if __name__ == "__main__":
    main(sys.argv[1:])