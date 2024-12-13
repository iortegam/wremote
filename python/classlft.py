#!/usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        classlft.py
#
# Purpose:
#         Class for lft
#          
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

import scipy.signal as sig

import scipy as sy
import scipy.fftpack as syfp
import glob



def ckDir(dirName,logFlg=False,exit=False):
    ''' '''
    if not os.path.exists( dirName ):
        print ('Input Directory %s does not exist' % (dirName))
        if logFlg: logFlg.error('Directory %s does not exist' % dirName)
        if exit: sys.exit()
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

def rms(residual):
    '''Calcuates the RMSE, 
       xData = observed data, yData = modeled data'''

    #--------------------------------
    # Make sure arrays are numpy type
    #--------------------------------
    residual = np.asarray(residual)

    #---------------------------------
    # Find the residual sum of squares 
    #---------------------------------
    SS_res = sum( (residual)**2 )

    #------------------------------
    # Root Mean Square Error (RMSE)
    #------------------------------
    rmse = np.sqrt( SS_res / len(residual) )

    return rmse


#------------------------------------------------------------------------------------------------------------------------------                     
class ReadOutputLFT():

    def __init__(self,pathDir):
        
        self.Dir = pathDir            
        
    def Readactparms(self):

        fName = self.Dir + '/actparms.dat'

        ckFile(fName, exit=True)

        self.parms = {}

        with open(fName) as fopen: lines = fopen.readlines()

        self.parms['tempFlg'] = int(lines[0].strip().split()[1])
        self.parms['presFlg'] = int(lines[1].strip().split()[1])
        self.parms['colFlg']  = int(lines[2].strip().split()[1])

        if self.parms['tempFlg'] >= 1: 
            self.parms['temp'] = float(lines[-1].strip().split()[1])
        
        if self.parms['presFlg'] >=1:
            self.parms['pres'] = lines[-1].strip().split()[2]

        if self.parms['colFlg'] >= 1:
            colFactor = []
            for i in range(0, self.parms['colFlg']):
                colFactor.append(float(lines[-1].strip().split()[2+i]))

            self.parms['colFactor'] = np.asarray(colFactor)

        self.actparmsFlg =  True

    def Readmodulat(self):

        fName = self.Dir + '/modulat.dat'

        ckFile(fName, exit=True)

        with open(fName) as fopen: lines = fopen.readlines()

        self.mod = {}

        self.mod['opd']          = [float(x.strip().split()[0]) for x in lines[1:] ]
        self.mod['Modulation']   = [float(x.strip().split()[1]) for x in lines[1:] ]
        self.mod['Phase']        = [float(x.strip().split()[2]) for x in lines[1:] ]

        self.ModFlg = True

    def Readilsret(self):

        fName = self.Dir + '/ilsre.dat'

        ckFile(fName, exit=True)

        with open(fName) as fopen: lines = fopen.readlines()

        self.ils = {}

        self.ils['opd']   = [float(x.strip().split()[0]) for x in lines[0:] ]
        self.ils['ils']   = [float(x.strip().split()[1]) for x in lines[0:] ]
      
        self.ilsFlg = True

    def Readcifg(self):

        fName = self.Dir + '/cifg.dat'

        ckFile(fName, exit=True)

        with open(fName) as fopen: lines = fopen.readlines()

        self.cifg = {}

        self.cifg['opd']          = [float(x.strip().split()[0]) for x in lines[1:] ]
        self.cifg['Real']         = [float(x.strip().split()[1]) for x in lines[1:] ]
        self.cifg['Imaginary']    = [float(x.strip().split()[2]) for x in lines[1:] ]

        self.cifgFlg = True


    def Readspecrec(self):

        listSpec = glob.glob(self.Dir + '/specre*')

        if len(listSpec) >=1:

            self.spc = {}

            self.spc['numMW'] = len(listSpec)

            for i, sp in enumerate(listSpec):

                fName = sp
                istr  = str(i)

                ckFile(fName, exit=True)

                with open(fName) as fopen: lines = fopen.readlines()

                self.spc.setdefault('wn_'+istr,[]).append([float(x.strip().split()[0]) for x in lines[0:] ])
                self.spc.setdefault('Obs_'+istr,[]).append([float(x.strip().split()[1]) for x in lines[0:] ])
                self.spc.setdefault('Fitted_'+istr,[]).append([float(x.strip().split()[2]) for x in lines[0:] ])
                self.spc.setdefault('Difference_'+istr,[]).append([float(x.strip().split()[3]) for x in lines[0:] ])
                self.spc.setdefault('rmse_'+istr,[]).append(rms([float(x.strip().split()[3]) for x in lines[0:] ]))
                
                maxY        = np.max(np.asarray(self.spc['Obs_'+istr]))
                Difference  = np.asarray(self.spc['Difference_'+istr])
                
                DifferenceP = (Difference / maxY) 

                self.spc.setdefault('DifferencePerc_'+istr,[]).append(DifferenceP[0] * 100. )
                self.spc.setdefault('rmsePerc_'+istr,[]).append(rms(DifferenceP[0]) * 100.)

            #------------------------
            # Convert to numpy arrays
            #------------------------
            for k in self.spc:
                self.spc[k] = np.asarray(self.spc[k])

                self.spcFlg = True
            
            

    def Readkernel(self):

        fName = self.Dir + '/kernel.dat'

        ckFile(fName, exit=True)

        self.kern = {}

        with open(fName) as fopen: lines = fopen.readlines()

        self.kern['kernel'] = np.array([[float(x) for x in row.split()] for row in lines]) 

        

#------------------------------------------------------------------------------------------------------------------------------        
class Plotlft(ReadOutputLFT):

    def __init__(self,pathDir, saveFlg=False, outFname=''):
        
        #------------------------------------------------------------
        # If outFname is specified, plots will be saved to this file,
        # otherwise plots will be displayed to screen
        #------------------------------------------------------------
        #if outFname: self.pdfsav = PdfPages(outFname)
        #else:        self.pdfsav = False

        self.Dir = pathDir  

        if saveFlg: 
            if ckDir(outFname,exit=False):
                os.remove(outFname) 
            self.pdfsav = PdfPages(outFname)
        else:        self.pdfsav = False

        self.modFlg = False
        
        #super(Plotlft,self).__init__(pathDir)

    def closeFig(self):
        self.pdfsav.close()


    def pltspectra(self):
        ''' Plot spectra and fit and Jacobian matrix '''
    
        print ('\nPlotting Linefit Retrieval...........\n')

        self.Readspecrec()

        #--------------------------------
        # Plot data for each micro-window
        #--------------------------------            
        for x in range(0, self.spc['numMW']):
            x = str(x)

            fig, (ax1, ax2)  = plt.subplots(2, figsize=(10,6), sharex=True)

            gs   = gridspec.GridSpec(2,1,height_ratios=[1,3])
            ax1  = plt.subplot(gs[0], sharex=ax2)
            ax2  = plt.subplot(gs[1],sharex=ax1)
            ax1.plot(self.spc['wn_'+x][0],self.spc['DifferencePerc_'+x][0],color='k', linewidth=1.5)
            ax1.axhline(y=0,color='r')
            ax1.grid(True)
            ax1.set_ylabel('Difference [%]', fontsize=14)
            ax1.set_title('Micro-Window {0:} (RMSe [%]  = {1:.4f})'.format(x, +self.spc['rmsePerc_'+x][0]), fontsize=14)
            ax1.set_xlim((np.min(self.spc['wn_'+x]),np.max(self.spc['wn_'+x])))
            ax1.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            ax1.xaxis.set_minor_locator(AutoMinorLocator())
            plt.tick_params(which='minor',length=4,color='b')
            
            ax2.plot(self.spc['wn_'+x][0],self.spc['Obs_'+x][0],label='Observed')
            ax2.plot(self.spc['wn_'+x][0],self.spc['Fitted_'+x][0],label='Fitted')
            
            ax2.grid(True)
            ax2.set_xlabel('Wavenumber [cm$^{-1}$]',  fontsize=14)
            ax2.set_ylabel('Transmission (Arbitrary)',  fontsize=14)
            #ax2.set_ylim(bottom=0.0)
            ax2.set_xlim((np.min(self.spc['wn_'+x]),np.max(self.spc['wn_'+x])))

            #ax2.legend(prop={'size':12},loc='upper center', bbox_to_anchor=(0.83, 0.94), fancybox=True, ncol=self.spc['numMW']+3)  
            ax2.legend(prop={'size':12},loc=4, ncol=self.spc['numMW']+3)#, bbox_to_anchor=(0.83, 0.94), fancybox=True, ncol=self.spc['numMW']+3)  
            ax1.tick_params(axis='x',which='both',labelsize=14)
            ax1.tick_params(axis='y',which='both',labelsize=14)
            ax2.tick_params(axis='x',which='both',labelsize=14)
            ax2.tick_params(axis='y',which='both',labelsize=14)

            fig.subplots_adjust(bottom=0.13,top=0.94, left=0.13, right=0.95)
   
            if self.pdfsav: self.pdfsav.savefig(fig,dpi=200)
            else:           plt.show(block=False)


    def pltils(self):
        ''' Plot spectra and fit and Jacobian matrix '''
    
        print ('\nPlotting Linefit ILS...........\n')

        self.Readilsret()

        OPD = np.asarray(self.ils['opd'])
        ils = np.asarray(self.ils['ils'])
      

        fig, (ax1, ax2)  = plt.subplots(1, 2, figsize=(10,6))

        ax1.plot(OPD, ils,color='r', linewidth=1.5)
        #ax1.axhline(y=0,color='r')
        #if len(self.dirLst) > 1: ax1.fill_between(self.spc['wn_'+x],self.spc['Difference_'+x]-self.spc['DifSTD_'+x],self.spc['Difference_'+x]+self.spc['DifSTD_'+x],alpha=0.5,color='0.75')
        ax1.grid(True)
        ax1.set_ylabel('Response', fontsize=14)
        ax1.set_xlabel('OPD [cm]', fontsize=14)
        #ax1.set_xlim((np.min(self.spc['wn_'+x]),np.max(self.spc['wn_'+x])))
        ax1.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ax1.xaxis.set_minor_locator(AutoMinorLocator())
        plt.tick_params(which='minor',length=4,color='b')

        ax1.set_title('ILS Ret', fontsize=14)
        
        ax2.plot(OPD, ils,color='r', linewidth=1.5)
        
        ax2.grid(True)
        #ax2.set_ylabel('Response', fontsize=14)
        ax2.set_xlabel('OPD [cm]', fontsize=14)
        ax2.set_ylim(top=np.max(ils)/2.)
        ax2.set_xlim((np.min(OPD) + abs(np.min(OPD)*0.75)), (np.max(OPD) - np.max(OPD)*0.75))
        ax2.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ax2.xaxis.set_minor_locator(AutoMinorLocator())

        ax1.tick_params(axis='x',which='both',labelsize=14)
        ax1.tick_params(axis='y',which='both',labelsize=14)
        ax2.tick_params(axis='x',which='both',labelsize=14)
        ax2.tick_params(axis='y',which='both',labelsize=14)

        ax2.set_title('ILS Ret (zoom-in)', fontsize=14)

        fig.subplots_adjust(bottom=0.1,top=0.94, left=0.11, right=0.95)

        if self.pdfsav: self.pdfsav.savefig(fig,dpi=200)
        else:           plt.show(block=False)

    def pltmod(self):
        ''' Plot spectra and fit and Jacobian matrix '''
    
        print ('\nPlotting Modulation/Phase ...........\n')

        self.Readmodulat()

        OPD = np.asarray(self.mod['opd'])
        Mod = np.asarray(self.mod['Modulation'] )
        Pha = np.asarray(self.mod['Phase'])
      

        fig, (ax1, ax2)  = plt.subplots(2, figsize=(10,6), sharex=True)

        ax1.plot(OPD, Mod,color='r', linewidth=2.5)
      
        ax1.grid(True)
        ax1.set_ylabel('Modulation', fontsize=14)
        #ax1.set_xlabel('OPD', fontsize=14)
        ax1.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
        ax1.xaxis.set_minor_locator(AutoMinorLocator())

        ax1.set_title('Modulation', fontsize=14)      
        ax1.tick_params(axis='x',which='both',labelsize=14)
        ax1.tick_params(axis='y',which='both',labelsize=14)
        ax1.set_ylim(0.9, 1.1)

        ax2.plot(OPD, Pha,color='r', linewidth=2.5)
      
        ax2.grid(True)
        ax2.set_ylabel('Phase [mr]', fontsize=14)
        ax2.set_xlabel('OPD [cm]', fontsize=14)
        ax2.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
        ax2.xaxis.set_minor_locator(AutoMinorLocator())
        ax2.set_ylim(-0.05, 0.05)

        ax2.set_title('Phase', fontsize=14)      
        ax2.tick_params(axis='x',which='both',labelsize=14)
        ax2.tick_params(axis='y',which='both',labelsize=14)
      
        fig.subplots_adjust(bottom=0.1,top=0.94, left=0.11, right=0.95)

        self.modFlg = True

        if self.pdfsav: self.pdfsav.savefig(fig,dpi=200)
        else:           plt.show(block=False)

    def pltcifg(self):
        ''' Plot spectra and fit and Jacobian matrix '''
    
        print ('\nPlotting cifg ...........\n')

        self.Readcifg()

        OPD  = np.asarray(self.cifg['opd'] )
        Real = np.asarray(self.cifg['Real'] )
        Imag = np.asarray(self.cifg['Imaginary'])


        fig, (ax1, ax2)  = plt.subplots(2, figsize=(10,6), sharex=True)

        ax1.plot(OPD, Real,color='r', linewidth=2.5)
      
        ax1.grid(True)
        ax1.set_ylabel('Real', fontsize=14)
        #ax1.set_xlabel('OPD', fontsize=14)
        ax1.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
        ax1.xaxis.set_minor_locator(AutoMinorLocator())

        ax1.set_title('Real', fontsize=14)      
        ax1.tick_params(axis='x',which='both',labelsize=14)
        ax1.tick_params(axis='y',which='both',labelsize=14)

        ax2.plot(OPD, Imag,color='r', linewidth=2.5)
      
        ax2.grid(True)
        ax2.set_ylabel('Imaginary', fontsize=14)
        ax2.set_xlabel('OPD [cm]', fontsize=14)
        ax2.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
        ax2.xaxis.set_minor_locator(AutoMinorLocator())

        ax2.set_title('Imaginary', fontsize=14)      
        ax2.tick_params(axis='x',which='both',labelsize=14)
        ax2.tick_params(axis='y',which='both',labelsize=14)
      
        fig.subplots_adjust(bottom=0.1,top=0.94, left=0.11, right=0.95)  

        if self.pdfsav: self.pdfsav.savefig(fig,dpi=200)
        else:           plt.show(block=False)

    def pltkernel(self):

        print ('\nPlotting Kernel...........\n')

        offs    = 32 # WHY 32?? --> Same as The IDL code lft.pro from Jim

        self.Readkernel()

        if not self.modFlg: self.Readmodulat()

        OPD     = np.asarray(self.mod['opd'])
        krn     = np.asarray(self.kern['kernel'])

        k = krn[offs:offs+20,offs:offs+20]

        fig, ax1 = plt.subplots(figsize=(8,5))

        for i in range(k.shape[0]):

            ax1.plot(OPD, k[i,:], linewidth=1.5)

        ax1.grid(True)
        ax1.set_ylabel('Kernels', fontsize=14)
        ax1.set_xlabel('OPD [cm]', fontsize=14)

        ax1.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ax1.xaxis.set_minor_locator(AutoMinorLocator())
        plt.tick_params(which='minor',length=4,color='b')

        ax1.set_title('Kernels', fontsize=14)
     
        ax1.set_xlabel('OPD [cm]', fontsize=14)     
        ax1.tick_params(axis='x',which='both',labelsize=14)
        ax1.tick_params(axis='y',which='both',labelsize=14)
       
        fig.subplots_adjust(bottom=0.11,top=0.94, left=0.11, right=0.95)

        if self.pdfsav: self.pdfsav.savefig(fig,dpi=200)
        else:           plt.show(block=False)

    def plttext(self, msg):
        ''' Plot spectra and fit and Jacobian matrix '''
    
        print ('\nShow text in Figure ...........\n')

        fig, ax = plt.subplots(figsize=(10,6))  

        for i, m in enumerate(msg):
            i += 1
            ax.text(0.0,0.9 - (i*0.05) ,m, ha='left', fontsize=10, color='b')

        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.axis('off')


        if self.pdfsav: self.pdfsav.savefig(fig,dpi=200)
        else:           plt.show(block=False)




if __name__ == "__main__":
    main()