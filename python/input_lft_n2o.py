#----------------------------------------------------------------------------------------
# Name:
#        input_lft.py
#
# Purpose:
#       This is the main input file for lft.py version 145. 
#
# Notes:
#       1) The input file is read in as a python file, therefore you should follow python
#          syntax when editing.
#       
# Version History:
#       Created, October, 2018  Ivan Ortega (iortega@ucar.edu)
#
#----------------------------------------------------------------------------------------

#------------
# Gas
#------------
gas          = 'N2O'

#------------
# Spectrum Name
#------------
spc           = 'N2O_InSb_35_140122-Av.0'

#------------
# Year
#------------
year          = '2022'

#--------------------
# Key input parameters during cell measurements
#--------------------
cellLength    = 2.07            # Cell Length in [cm]                              					 
aperture      = 1.3            # Aperture in [mm]
foclength     = 418.0		    # Foc Length in [mm]
maxopd        = 257.0			# Max OPD in [cm]

ResampFlg     = False           # Flag for resampling
Resamp        = 8				# if Flag is True number for resampling	

#--------------------
# Flag to run LINEFIT, if false will try to plot previous files if they exist
#--------------------
lftFlg        = True 

                                                        #--------------------------#
                                                        # Below are standard paths-#
                                                        #--------------------------#

#------------
# Base directory
#------------
pathDir      = 'C:/ils/lft145_'+gas.lower()                

#--------------------
# Path  of spectrum
#--------------------
spcDir        = r"C:\IR-Data\\"+gas.upper()+"\\"+year
#-------------------------
# linefit default input file
#-------------------------
DefaultInp   = 'C:/ils/lft145_'+gas.lower()+'/lft14.inp-default-'+gas.lower()

#-------------------------
# linefit executable file
#-------------------------
lfit         = 'C:/LINEFITcodes/lft145/lft145.exe'


                       
