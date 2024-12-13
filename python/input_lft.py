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
gas          = 'HBr'

#------------
# Spectrum Name
#------------
spc           = 'HBr_InSb_87_KBr_111024.0'

#------------
# Year
#------------
year          = '2024'

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
pathDir      = r'C:\\Users\\bldopus\\wremote\\Admin\\BLD\\ils\\lft145_'+gas.lower()                

#--------------------
# Path  of spectrum
#--------------------
#spcDir        = r"C:\IR-Data\\"+gas.upper()+"\\"+year
spcDir        = r'C:\\Users\\bldopus\\wremote\\Admin\\BLD\\IR-Data\\'+gas.upper()+"\\"+year
#-------------------------
# linefit default input file
#-------------------------
DefaultInp   = pathDir + '\\lft14.inp-default-'+gas.lower()

#-------------------------
# linefit executable file
#-------------------------
#lfit         = 'C:/LINEFITcodes/lft145/lft145.exe'
lfit          = r'C:\\Users\\bldopus\\wremote\\Admin\\LINEFITcodes\\lft145\\lft145.exe'


                       
