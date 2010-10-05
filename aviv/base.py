__description__ = """"""
__author__ = "Michael J. Harms"
__date__ = ""

import sys, os
import parsers

class AvivError(Exception):
    """
    General error class for this module.
    """

    pass


class ConfigAttribute:
    """
    Class that holds information to parse and  configuration information
    from an Aviv experiment file.
    """
    
    def __init__(self,aviv_key,name,title,type,format):
        """
        aviv_key: $SOME_VARIABLE in Aviv file
        name: the local name for this configuration
        title: the title of the variable that will be dumped to the pretty
               output file
        type: the variable type (str, float, int)
        format: the output format of the variable
        """
        
        self.aviv_key = aviv_key
        self.name = name
        self.title = title
        self.type = type
        self.format = format


class Channel:
    """
    Class to process a single output channel from an experiment.  Whenever a 
    method is called to process the signal, it writes over self.y and possibly
    self.y_err.  It also saves a copy of the signal after processing as an 
    attribute (listed in the method doc string).  All methods return a string
    describing what occured that can be placed in the output file header.
    """

    def __init__(self,name,x,y,y_err=None,concentrations=None,dark_signal=None,
                 qc_signal=None,shot_size=None):
        """
        Initialize instance of class. 

        Creates self.raw_x, self.raw_signal, self.raw_err
        """

        self.name = name
        self.x = x[:]
        self.y = y[:]

        if len(self.x) == 0 or len(self.y) == 0:
            err = "No x or y values recorded for channel %s\n" % self.name
            raise AvivError(err)

        # If optional arguments are not specified, create sane "neutral"
        # defaults that will not alter the signal if they are used in a 
        # processing step.   
        if y_err == None:
            self.y_err = [0. for s in self.y]
        else:
            self.y_err = y_err[:]
        
        if concentrations == None:
            self.concentrations = [1. for s in self.y]
        else:
            self.concentrations = concentrations[:] 
 
        if dark_signal == None:
            self.dark_signal = [0. for s in self.y]
        else:
            self.dark_signal = dark_signal[:]

        if qc_signal == None:
            self.qc_signal = [1. for s in self.y]
        else:
            self.qc_signal = qc_signal[:]

        if shot_size == None:
            self.shot_size = [0. for s in self.y]
        else:
            self.shot_size = shot_size[:]

        # Record raw signals
        self.raw_x = self.x[:]
        self.raw_signal = self.y[:]
        self.raw_err = self.y_err[:]

    def correctDarkQC(self):
        """
        Correct for dark and qc signals.  

        Creates self.qc_corr
        """

        self.qc_corr = [(s - self.dark_signal[i])/self.qc_signal[i]
                        for i, s in enumerate(self.y)]
        self.y = self.qc_corr[:]
        
        return "Corrected with QC and dark signals\n"
 

    def correctTitrantBlanks(self,buf_blank,titr_blank):
        """
        Correct for dilution and buffer/titrant blanks.

        Creates self.corr_signal.
        """

        # Do buffer correction
        buffer_signal = buf_blank
        titrant_signal = titr_blank - buffer_signal
        corr_signal = [s-buffer_signal-titrant_signal*(1-self.concentrations[i])
                       for i, s in enumerate(self.y)]

        self.corr_signal = corr_signal[:]
        self.y = self.corr_signal[:]

        # Create output 
        out = ["Titrant Blank Correction:\n"]
        out.append("    Buffer blank: %.3F\n" % buf_blank)
        out.append("    Titrant blank: %.3F\n" % titr_blank)

        return "".join(out)

    def correctDilution(self):
        """
        Correct for dilution. 

        Creates self.dilution_corr_signal.
        """

        self.dilution_corr_signal = [y/self.concentrations[i]
                                     for i, y in enumerate(self.y)]
        self.y = self.dilution_corr_signal[:]

        return "Corrected signal for dilution\n"


    def correctDenaturant(self,instrument_values,init_conc=None,
                          titrant_conc=None,cell_vol=None):
        """
        Correct the denaturant concentration in the file by correcting some or
        all of the following: the initial titrant concentration (M), the titrant
        concentration (M) and the cell volume (mL).  

        creates self.denat_corr_x
        """
 
        input_values = [init_conc,titrant_conc,cell_vol]
        instrument_values = [v.value for v in instrument_values]

        # Make sure that the values specified will actually do a denaturant
        # correction
        if input_values == instrument_values or input_values == 3*[None]:
            self.denat_corr_x = self.x[:]
            return ""

        # Decide whether to use values from self or argument list
        if init_conc == None:
            init_conc = instrument_values[0]
        if titrant_conc == None:
            titrant_conc = instrument_values[1]
        if cell_vol == None:
            cell_vol = instrument_values[2]

        # Perform correction
        try:
            titrant = [init_conc]
            shot_size = [s/1000 for s in self.shot_size]
            for i in range(1,len(self.shot_size)):
                titr = titrant[i-1]*(cell_vol - shot_size[i])/cell_vol
                titr = titr + shot_size[i]*titrant_conc/cell_vol
                titrant.append(titr)
        except ValueError:
            err = "Invalid denaturant correction value specified!\n"
            raise AvivModuleError(err) 

        # Update with new titrant concentrations
        self.x = titrant[:]
        self.denat_corr_x = titrant[:]

        # Create logfile output
        out = ["Denaturant Correction:\n"]
        out.append("  Initial concentration: %.3F --> %.3F\n" %\
                   (instrument_values[0],init_conc))
        out.append("  Titrant concentration: %.3F --> %.3F\n" %\
                   (instrument_values[1],titrant_conc))
        out.append("  Cell volume:           %.3F --> %.3F\n" %\
                   (instrument_values[2],cell_vol))

        return "".join(out)


    def subtractBlank(self,blank_file=None):
        """
        Subtract the blank signal from a channel.

        Creates self.blanked.
        """

        if blank_file != None:
            blank_exp = parsers.preParse(blank_file)
        else:
            self.blanked = self.y[:]
            return "No blank correction done!\n" 

        if self.x != blank_exp.channel_list[0].raw_x:
            err = "Blank file and input file do not match!"
            raise AvivError(err)

        tmp_x = [s - blank_exp.channel_list[0].raw_signal[i]
                 for i, s in enumerate(self.y)]
        self.blanked = tmp_x[:]

        self.y = self.blanked[:]   
    
        return "Removed blank (\"%s\")\n" % blank_file

 

    def convertToMME(self,num_residues,molec_weight,initial_conc,path_length):
        """
        Converts signal to Mean Molar Ellipticity.

        Creates self.MME, self.MME_err
        """

        # Create list of MME corrections using concentrations and protein
        # information
        MME_corr = (100.0*molec_weight)/(path_length*initial_conc*num_residues)

        # Convert signal and error to MME
        len_data = len(self.y)
        self.MME = [self.y[i]*MME_corr for i in range(len_data)]
        self.MME_err = [self.y_err[i]*MME_corr for i in range(len_data)]
        
        self.y = self.MME[:]
        self.y_err = self.MME_err[:]       

        # Write out data file processing data
        out = ["MME converstion:\n"]
        out.append("  Initial concentration (ug/mL): %8.3F\n" % initial_conc)
        out.append("  Number of residues:            %8i\n" % num_residues)
        out.append("  Molecular weight (Da):         %8i\n" % molec_weight)
        out.append("  Path length (cm):              %8.3F\n" % path_length)

        return "".join(out)

    def normalizeSignal(self,invert=False):
        """
        Normalize signal from 0 to 1.  If invert == True, invert the signal.

        Creates self.norm_signal, self.norm_err.
        """

        # Normalize the signal
        maximum = max(self.y)
        minimum = min(self.y)
        self.norm_signal = [(s-minimum)/(maximum-minimum) for s in self.y]

        # Invert the signal if required
        if invert:
            maximum = max(self.norm_signal)
            self.norm_signal = [-s + maximum for s in self.norm_signal]

        # Generate normalized error
        self.norm_err = [self.y_err[i]*self.norm_signal[i]/self.y[i]
                         for i in range(len(self.y))]
        
        self.y = self.norm_signal[:]
        self.y_err = self.norm_err[:]

        return ""

class Parser:
    """
    This provides the __init__ function for the individual types of parser
    classes.  The same protocol protocol is run, no matter the instrument
    or experiment types.  The specific functions are determined by the 
    daughter class in question.
    """

    def __init__(self,**kwargs):
        """
        Initialize instance of class.  The kwarg values will depend on the
        class that inherits this one.  
        """

        self.config_extract = []
        self.data_extract = {}
        
        # Experiment-specific data that may or may not be extracted; put a 
        # dummy here in case it is used.
        self.concentrations = None
        self.shot_size = None
        
        try:
            self.experiment_kwargs
        except AttributeError:
            self.experiment_kwargs = []
        
        try:
            self.instrument_kwargs
        except AttributeError:
            self.instrument_kwargs = []

  
    def processFile(self,**kwargs):
        
        if "input_file" not in kwargs.keys():
            err = "input_file key must be specified!\n"
            raise AvivError(err)
  
        # Initialize data to be extracted
        self.setupInstrumentExtraction(**kwargs)
        self.setupExperimentExtraction(**kwargs)

        # Load in experiment, extracting data
        header = []
        self.loadExperiment(kwargs["input_file"])
        header.append(self.createConfigHeader())
        # Process each channel
        self.grabChannels()
        header.append(self.processChannels(**kwargs))

        data_out = self.createOutput()

        header = "".join(header)
        header = header.split("\n")
        header = "".join(["# %s\n" % l for l in header])

        self.out = "".join([header,data_out])

    def finalOutput(self):
        """
        Return pretty output.
        """
        
        return self.out
        
