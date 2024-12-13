#---------------------------
# General suggested items to follow for installation on Win PC
#---------------------------

- Create a folder called "xxxopus" inside C:\Users, where "xxx" is your three letters id for your site; For example, in our case we have "bldopus" for Boulder

- Copy the "wremote" folder in the google drive inside the above folder: For example: C:\Users\bldopus\wremote

- The main python script to start a set of measurements is "measureSet_Onsala.py"
    There are a couple of modifications you need to follow:
        - Open "measureSet_Onsala.py" and edit in main the user name (~line 78)
        - Currently, the script has the standard names of xpm in Boulder. Likely you are using different names and filters; change the names in lines ~376

- There are  additional python files needed: 'remoteData', 'opusIO', 'WebParser' 'ckpy_Onsala'. 
  There is a single line you need to modify on each file: check the "Edit here only". Check also the bat files with the same names and edit them with the correct path.

- Note that you may need to install some python packages. The easiest way to know what packages is just to run the measureSet_Onsala.py and check for messages.

- There is a local input file here: C:\Users\xxxopus\wremote\local.input, modify it accordingly

- There is another control file with more inputs. I created one for onsala, see XXX_Defaults.input (change the XXX with your three letters id). For Boulder we have: C:\Users\bldopus\wremote\bin\ops\FL0_Defaults.input
Open this file and modify the inputs.

- The macros we use are here: C:\Users\bldopus\wremote\Macro\BLD
   Three macros are used: one for InSb. one for MCT, and one for testing. 
   You may need to modify gain, but for now no worries about it.

- Our XPM files are here: C:\Users\bldopus\wremote\XPM\Solar

- I may be forgetting something but give it a try and let me know. Run the measureSet_Onsala.py and let me know how it goes. 