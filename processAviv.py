#!/usr/bin/env python
__author__ = "Michael J. Harms"
__date__ = "070614"
__description__ = \
"""
A Tkinterface that allows users to fit Aviv experimental data in an intuitive
and robust way.
"""

# Import python standard modules
import sys, os

# Import Tk modules
try:
    from Tkinter import *
    import FileDialog, tkMessageBox, Dialog
except ImportError:
    print "TK required!"
    sys.exit()

# Import program modules
from tkModule import *
import aviv, denaturantModule 
from aviv.parsers import *

BUFFER_OPTIONS = ["K Acetate",
                  "Na Acetate",
                  "MES",
                  "HEPES",
                  "TAPS",
                  "CHES",
                  "CAPS",
                  "MOPS",
                  "Tris"]

SALT_OPTIONS = ["KCl",
                "NaCl"]

PROTEIN_OPTIONS = ["D+PHS",
                   "PHS",
                   "NVIAGA",
                   "D+PHSt",
                   "WT"]

TITRANT_OPTIONS = ["GdmHCl",
                   "Urea"]

PHTITR_OPTIONS = ["KOH",
                  "NaOH",
                  "HCl"]

DENAT_ERR_CUTOFF = 0.05

class MainWindow:
    """
    Main window that controls the program.
    """

    def __init__(self,parent):
        """
        Initialize main window.
        """

        # Initialize window
        self.parent = parent
        self.parent.title("Process Aviv experiment file")

        # Add "File" menu
        menu_bar = Menu(self.parent)
        file_menu = Menu(menu_bar,tearoff=0)
        file_menu.add_command(label="Open...",command=self.loadFileDialog)
        file_menu.add_command(label="Exit",command=self.parent.quit)
        menu_bar.add_cascade(label="File",menu=file_menu)
        self.parent.config(menu=menu_bar)

        self.frame = Frame(padx=10,pady=10)
        self.frame.grid()

        start_text = "Open an Aviv experiment file (.dat) to begin."
        self.start_label = Label(self.frame,text=start_text)
        self.start_label.grid()

        # If a file is specified on the command line, try to open it
        try:
            self.input_file = sys.argv[1]
            self.loadFile()
        except IndexError:
            pass


    def loadFileDialog(self):
        """
        Use the built in load file dialog to load a filename into
        input_file_entry.
        """

        # Use LoadFileDialog to let user select file
        d = FileDialog.LoadFileDialog(self.parent)
        self.input_file = d.go(".","*.dat")
        if self.input_file != None:
            self.loadFile()

    def loadFile(self):
        """
        Do initial loading of input file and call dialog that will allow user
        to input appropriate information about experiment.
        """

        #Check to make sure the file exists
        if not os.path.isfile(self.input_file):

            if self.input_file == "" or self.input_file == None:
                err = "You need to specify an input file to perform a fit!"
            else:
                err = "Could not find: \"%s\"" % self.input_file

            tkMessageBox.showerror(title="File does not exist!",message=err)


        # Create an instance of AvivExp based on contents of input file
        try:
            self.tmp_exp = preParse(self.input_file)
            self.populateExpParam()
        except AvivError, value:
            tkMessageBox.showerror(title="Problem with input file",
                                   message=value)


    def loadBlankFile(self):
        """
        """

        d = FileDialog.LoadFileDialog(self.parent)
        blank_file = d.go(".","*.dat")
        if blank_file != None:
            self.blank_entry.entry.delete(0,END)
            self.blank_entry.entry.insert(0,blank_file)
            self.blank_entry._checkObject()


    def populateExpParam(self):
        """
        Pre-read specified file to determine the experiment type, then create
        a form correct for the experiment type.
        """

        # Clear form
        keep_obj = ["input_file","tmp_exp","parent"]
        to_destroy = [k for k in self.__dict__.keys() if k not in keep_obj]
        for k in to_destroy:
            obj = self.__dict__.pop(k)
            try:
                obj.destroy()
            except AttributeError:
                pass

        #self.frame.destroy()
        self.frame = Frame(self.parent)
        self.frame.grid()

        # ----- Information extracted from file -----
        self.filename_label = Label(self.frame,
                                 text="File: %s" % self.tmp_exp.input_file)
        self.filename_label.grid(sticky=W)

        self.instrument_label = Label(self.frame,text=\
                                  "Instrument: %s" % self.tmp_exp.instrument)
        self.instrument_label.grid(sticky=W)

        self.exp_label = Label(self.frame,text=\
                                  "Experiment: %s" % self.tmp_exp.exp_type)
        self.exp_label.grid(sticky=W)
        self.name_label = Label(self.frame,text=\
                               "Name: %s" % self.tmp_exp.name.value)
        self.name_label.grid(sticky=W)
        self.descript_label = Label(self.frame,text="Description: %s" % \
                                    self.tmp_exp.description.value)
        self.descript_label.grid(sticky=W)

        Divider(self.frame,arrangement="h")


        # ----- Entries common to all experiment types -----
        self.user = EntryBox(self.frame,str,"User initials:",tag="user")
        self.user.grid(sticky=W)

        # Create objects to grab date
        self.date_frame = Frame(self.frame)

        self.date_label = StandardLabel(self.date_frame,
                                        label_text="Date (Y M D):")
        self.year = EntryBox(self.date_frame,entry_type=int,
                             value_limits=[1989,2100],
                             entry_default=self.tmp_exp.raw_date[2],
                             tag="year")
        self.year.config(width=4)
        self.month = EntryBox(self.date_frame,entry_type=int,
                              value_limits=[1,12],
                              entry_default=self.tmp_exp.raw_date[0],
                              tag="month")
        self.month.config(width=2)
        self.day = EntryBox(self.date_frame,entry_type=int,
                            value_limits=[1,31],
                            entry_default=self.tmp_exp.raw_date[1],
                            tag="day")
        self.day.config(width=2)

        self.date_label.grid(row=0,column=0)
        self.year.grid(row=0,column=1)
        self.month.grid(row=0,column=2)
        self.day.grid(row=0,column=3)
        self.date_frame.grid(sticky=W)

        # ----- Wavelength scan widgets -----
        if self.tmp_exp.exp_type == "Wavelength":
            self.blank_frame = Frame(self.frame)
            self.blank_entry = EntryBox(self.blank_frame,entry_type=str,
                                        entry_default="",
                                        entry_width=30,
                                        label_text="Blank file",
                                        tag="blank_file")
            self.load_blank_button = Button(self.blank_frame,text="...",
                                            command=self.loadBlankFile)
            self.blank_entry.grid(row=0,column=0,sticky=W)
            self.load_blank_button.grid(row=0,column=1,sticky=W)

            self.blank_frame.grid(sticky=W)

        Divider(self.frame,arrangement="h")

        # ----- Titration-specific widgets -----
        if self.tmp_exp.exp_type == "Titration":
            self.denat_frame = Frame(self.frame)
            self.init_conc = EntryBox(self.denat_frame,entry_type=float,
                entry_default=self.tmp_exp.init_conc.value,
                label_text="Initial [denaturant] (M)",label_width=24,
                tag="init_conc")

            self.titrant_conc = EntryBox(self.denat_frame,entry_type=float,
                entry_default=self.tmp_exp.titrant_conc.value,
                label_text="Titrant [denaturant] (M)",label_width=24,
                tag="titrant_conc")
            
            self.cuvette_volume = EntryBox(self.denat_frame,entry_type=float,
                entry_default=self.tmp_exp.cell_vol.value,
                label_text="Sample volume (mL)",label_width=24,
                tag="cell_vol")
            
            self.init_conc.grid(sticky=W)
            self.titrant_conc.grid(sticky=W)
            self.cuvette_volume.grid(sticky=W)
            self.denat_frame.grid(sticky=W)            

            Divider(self.frame,arrangement="h")

        # ATF-specific widgets
        if self.tmp_exp.instrument == "ATF":
            self.do_qc_corr = CheckButton(self.frame,
                                label_text="Apply QC & dark corrections")
            self.do_qc_corr.grid()
            self.do_qc_corr.addTag("qc_corr")


            Divider(self.frame,arrangement="h")


        # ----- Set up channel panes -----
        pane_objects = []

        # Objects common to all experiments
        pane_objects.append((OptionBox,{"label_text":"Background:",
                                        "option_list":PROTEIN_OPTIONS,
                                        "tag":"protein_bg"}))
        pane_objects.append((EntryBox,{"entry_type":str,
                                        "label_text":"Mutation:",
                                        "allow_blank":True,
                                        "tag":"mutation"}))
        
        pane_objects.append((EntryBox,{"entry_type":float,
                                      "label_text":"Protein conc\n(ug/mL):",
                                      "tag":"protein_conc"}))

        # Instrument-specific objects
        if self.tmp_exp.instrument == "CD":
            pane_list = ["Sample"]
            pane_objects.append((EntryBox,{"entry_type":float,
                                           "label_text":"MW (Da):",
                                           "entry_default":16116,
                                           "tag":"molec_weight"}))
            pane_objects.append((EntryBox,{"entry_type":int,
                                           "label_text":"# residues:",
                                           "entry_default":143,
                                           "tag":"num_residues"}))
            pane_objects.append((EntryBox,{"entry_type":float,
                                           "label_text":"path (cm):",
                                           "entry_default":1,
                                           "tag":"path_length"}))

        elif self.tmp_exp.instrument == "ATF":

            # If no experimental data exist for the sample or reference, don't
            # make a pane for them.

            pane_list = []

            if self.tmp_exp.grab_sample:
                pane_list.append("Sample")
            if self.tmp_exp.grab_reference:
                pane_list.append("Reference")

            if len(pane_list) == 0:
                err = "File does not contain experimental data!\n"
                tkMessageBox.showerror(title="Problem with input file",
                                        message=value)



        # Experiment-specific objects 
        if self.tmp_exp.exp_type == "pH":
            pane_objects.append((OptionBox,{"label_text":"Titrant",
                                             "option_list":PHTITR_OPTIONS,
                                             "tag":"titrant_type"}))

        elif self.tmp_exp.exp_type == "Titration":
            pane_objects.append((OptionBox,{"label_text":"Titrant",
                                            "option_list":TITRANT_OPTIONS,
                                            "tag":"titrant_type"}))
            pane_objects.append((EntryBox,{"entry_type":float,
                                           "label_text":"Buffer blank",
                                           "tag":"buf"}))
            pane_objects.append((EntryBox,{"entry_type":float,
                                           "label_text":"Titrant blank",
                                           "tag":"titr"}))
            pane_objects.append((EntryBox,{"entry_type":float,
                                           "label_text":"Final n",
                                           "tag":"final_n"}))
            pane_objects.append((EntryBox,{"entry_type":float,
                                           "label_text":"Buffer n",
                                           "tag":"buffer_n"}))

        if self.tmp_exp.exp_type != "pH":
            pane_objects.append((EntryBox,{"entry_type":float,
                                           "label_text":"Final pH",
                                           "tag":"final_pH"}))
        # Buffer objects
        pane_objects.append((Divider,{"arrangement":"h"}))
        pane_objects.append((StandardLabel,
                             {"label_text":"Buffer components (mM)"}))
        pane_objects.append((MultiObject,{"contained_class":EntryOptBox,
                                          "num_objects":1,
                                          "entry_default":25,
                                          "entry_type":float,
                                          "option_list":BUFFER_OPTIONS,
                                          "dynamic":True,
                                          "arrangement":"v",
                                          "tag":"buffers"}))

        # Salt objects
        pane_objects.append((Divider,{"arrangement":"h"}))
        pane_objects.append((StandardLabel,
                             {"label_text":"Salt components (mM)"}))
        pane_objects.append((MultiObject,{"contained_class":EntryOptBox,
                                          "num_objects":1,
                                          "entry_default":100,
                                          "entry_type":float,
                                          "option_list":SALT_OPTIONS,
                                          "dynamic":True,
                                          "arrangement":"v",
                                          "tag":"salts"}))

        # Create MultiPane object that holds all of these data
        self.channels = MultiPane(self.frame,pane_list,pane_objects)
        self.channels.grid()

        Divider(self.frame,arrangement="h")

        # ----- Box for other comments ----- #
        self.comment_label = StandardLabel(self.frame,
                                           label_text="Other comments:")
        self.comment_label.grid()
        self.comment_text = TextWithScroll(self.frame,width=50,height=6,
                                           tag="comment_text")
        self.comment_text.grid()

        Divider(self.frame,arrangement="h")

        # ----- Process button -----
        self.process_button = Button(self.frame,text="Save processed file...",
                                command=self.processForm)
        self.process_button.grid(sticky=E)
        
    def raiseError(self,err):
        """
        Raise an error if the user has not filled out form correctly.
        """

        tkMessageBox.showerror(title="Invalid entry!",message=err)

    def processForm(self):
        """
        Take data from form, do processing, create header, then save file.
        """

        self.main_input = {}
        for k in self.__dict__.keys():

            # Only grab tagged objects
            try:
                tag = self.__dict__[k].getTag()
            except AttributeError:
                continue

            # Make sure that the entry is valid
            if not self.__dict__[k].isValid():
                err = "\"%s\" entry is not valid!" % tag
                self.raiseError(err)
                return 1

            self.main_input[tag] = self.__dict__[k].get()

        print self.main_input
        
        # Make sure that channel output is valid
        if not self.channels.isValid():
            err = "Invalid entry!"
            self.raiseError(err)
            return 1

        # Grab values from channels
        values = self.channels.get()
        if len(values.keys()) == 0:
            err = "At least one channel must be specified!" 
            self.raiseError(err)
            return 1

        # Grab tags from channels and use to create nested dictionary for 
        # further data processing
        tags = self.channels.getTags()

        # Decide which channels we are sending to the instrument parser
        self.to_parser = [("input_file",self.input_file)]
        if "Sample" in values.keys():
            self.to_parser.append(("sample",True))
        if "Reference" in values.keys():
            self.to_parser.append(("reference",True))
        
        # Combine tag and value output, renaming a few tags to pass to the
        # parser.
        self.channel_input = dict([(k,[]) for k in values.keys()]) 
        for c in values.keys():
            to_rename = ["titr","buf"]
            for t in to_rename:
                try:
                    position = tags[c].index(t)
                    tags[c][position] = "%s_%s" % (c[:3].lower(),t)
            
                    self.to_parser.append((tags[c][position],
                                           values[c][position]))

                except ValueError:
                    pass

            self.channel_input[c] = dict(zip(tags[c],values[c]))

        if self.tmp_exp.instrument == "ATF":
            self.to_parser.append(("qc_corr",self.main_input["qc_corr"]))
        
        if self.tmp_exp.instrument == "CD":
            self.to_parser.append(("protein_conc",
                                  self.channel_input["Sample"]["protein_conc"]))
            self.to_parser.append(("num_residues",
                                  self.channel_input["Sample"]["num_residues"]))
            self.to_parser.append(("molec_weight",
                                  self.channel_input["Sample"]["molec_weight"]))
            self.to_parser.append(("path_length",
                                  self.channel_input["Sample"]["path_length"]))

        if self.tmp_exp.exp_type == "Wavelength":
            self.to_parser.append(("blank_file",self.main_input["blank_file"]))

        # Use to_parser dictionary to parse the file
        self.to_parser = dict(self.to_parser)
        self.to_parser.update(self.main_input)     
 
        print self.to_parser
 
        try: 
            self.processExperiment()
        except AvivError, value:
            tkMessageBox.showerror(title="Problem with input file",
                                   message=value)

        # Create header
        self.createHeader()

        # Combine output
        output_lines = self.final_output.split("\n")
        output_lines = ["%s\n" % l for l in output_lines]
        self.combined_out = "".join(["".join(output_lines[:4]),self.header,
                                     "".join(output_lines[5:])])
        
        # Save output
        self.saveOutput() 

    def processExperiment(self):
        """
        Process experiment.  Populates self.final_experiment and
        self.final_output.
        """

        # Select the correct parser class
        parser = available_parsers[self.tmp_exp.exp_id]
       
        # Do parsing 
        self.final_experiment = parser()
        self.final_experiment.processFile(**self.to_parser)
        self.final_output = self.final_experiment.finalOutput()
        
        
    
    def createHeader(self):
        """
        Create a header describing experiment/instrument setup.

        Populates self.header
        """

        out = []

        # Process user and date
        out.append("# User: %s\n" % self.main_input["user"])
        date = "%i.%i.%i" % (self.main_input["year"],
                             self.main_input["month"],
                             self.main_input["day"])
        out.append("# Date: %s\n" % date)

        # Process comments
        comments = self.main_input["comment_text"]
        if comments != None:
            comments = comments.split("\n")
            comment_out = []
            for line in comments:
                if len(line) > 77:
                    space_cut = line.split()
                    first_entry = 0
                    total_line_length = 0
                    for i, x in enumerate(space_cut):
                        total_line_length += len(x) + 1
                        if total_line_length > 78:
                            out_line = " ".join(space_cut[first_entry:i])
                            comment_out.append(out_line)
                            first_entry = i
                            total_line_length = len(x)
                else:
                    comment_out.append(line)

            comment_out = ["# %s\n" % c for c in comment_out]

            out.append("# Comments:\n")
            out.extend(comment_out)

        out.append("# \n")
        
        # Channel-specific setup
        for c in self.channel_input.keys():
            inp = self.channel_input[c]

            out.append("# ----- %s channel experimental setup -----\n" % c)
            
            bg = inp["protein_bg"]
            m = inp["mutation"]
            if m != "":
                out.append("# Protein: %s/%s\n" % (bg,m))
            else:
                out.append("# Protein: %s\n" % bg)
            
            out.append("# Concentration: %.1F\n" % inp["protein_conc"])   

            # System pH
            if self.final_experiment.exp_type != "pH":
                out.append("# Final pH: %.2F\n" % inp["final_pH"])
          
            # Buffer components.  (This and the salt components section is a
            # bit of a hack.  If a single buffer is specified, inp["buffers"]
            # will be a tuple.  If more than one buffer is specified, it will 
            # be a tuple of tuples.  Argh.
            if len(inp["buffers"]) != 0:

                out.append("# Buffers:\n")
                try:
                    out.append("#     %.1F mM %s\n" % (inp["buffers"][0],
                                                       inp["buffers"][1]))   
                except TypeError: 
                    for b in inp["buffers"]:
                        out.append("#     %.1F mM %s\n" % (b[0],b[1]))   

            # Salt components                           
            if len(inp["salts"]) != 0:
                out.append("# Salts:\n")
                try:
                    out.append("#     %.1F mM %s\n" % (inp["salts"][0],
                                                       inp["salts"][1]))   
                except TypeError: 
                    for b in inp["salts"]:
                        out.append("#     %.1F mM %s\n" % (b[0],b[1]))   

            # Titrant data
            no_titrant_exp = ["Wavelength","Temperature"]
            if self.final_experiment.exp_type not in no_titrant_exp:
                t_type = inp["titrant_type"]
                out.append("# Titrant type: %s\n" % inp["titrant_type"])
            
            # For titration experiment, calculate final titrant conc using
            # Pace polynomial and compare to experiment.
            if self.final_experiment.exp_type == "Titration":
                buffer = inp["buffer_n"]
                final = inp["final_n"]           
  
                final_conc = denaturantModule.calcDenaturantConc(t_type,
                                                                 buffer,
                                                                 final)
                out.append("# Buffer n: %.4F\n" % buffer)
                out.append("# Final n: %.4F\n" % final)
                out.append("# Calculated [%s]: %.2F\n" % (t_type,final_conc))

                conc_in_exp = self.tmp_exp.channel_list[0].x[-1]
                if abs(final_conc - conc_in_exp) > DENAT_ERR_CUTOFF:
                    out.append("# Warning: final denaturant concentration ")
                    out.append("is incorrect\n")     
                
            out.append("#\n")

        self.header = "".join(out) 

    def saveOutput(self):
        """
        Save output to file using SaveFileDialog.
        """
        
        # Use SaveFileDialog to let user select file
        d = FileDialog.SaveFileDialog(self.parent)
        self.output_file = d.go(key="test")

        # Save file
        f = open(self.output_file,'w')
        f.write(self.combined_out)
        f.close()

# Start the main loop
if __name__ == "__main__":
    root = Tk()
    app = MainWindow(root)
    root.mainloop()

