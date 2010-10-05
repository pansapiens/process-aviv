__description__ = """"""
__author__ = "Michael J. Harms"
__date__ = ""

import os, sys
from base import *

# A dictionary of alternate column names for when Aviv changes the names of 
# their data columns randomly.
ALTERNATE_COLUMN_KEYS = {"CD_Error":"Error"}

class Aviv:
    """
    Class that allows for parsing and processing of general Aviv experiment
    files.
    """

    def loadExperiment(self,input_file):
        """
        Load all data from an Aviv experiment.
        """
       
        # Load data from file
        self.input_file = input_file
        self.loadFile()

        # Extract configuration
        self.extractConfiguration()

        # Extract data
        self.extractData()


    def loadFile(self):
        """
        Open and read an Aviv experiment file.  Does some basic sanity
        checking.
        """

        # Make sure file exists
        if not os.path.isfile(self.input_file):
            err = "\"%s\" does not exist!" % self.input_file
            raise AvivError(err)

        # Read in contents of file
        f = open(self.input_file,'r')
        self.file_contents = f.readlines()
        f.close()

        # Create simple list of keys that allows me to rapidly search file for
        # entries.
        self.file_keys = [l[0:6].strip() for l in self.file_contents]

        # Determine the instrument type
        if "$PMTHV" in self.file_keys:
            instrument_from_file = "ATF"
        elif "$CDHV:" in self.file_keys:
            instrument_from_file = "CD"
        else:
            err = "Instrument type in file (%s) is not recognized!" % \
                instrument_from_file
            raise AvivError(err)

        # See if the instrument type has been specified previously and verify 
        # that they match
        try:
            if self.instrument != instrument_from_file:
                err = "Instrument type does not match parsing class!"
                raise AvivError(err)
        except AttributeError:
            self.instrument = instrument_from_file

        # Determine the experiment type
        exp_type_from_file = self.file_contents[1].split(":")
        exp_type_from_file = exp_type_from_file[-1].strip()

        # See if exp type was specified previously and verify that they match
        try:
            if self.exp_type != exp_type_from_file:
                err = "Experiment type does not match parsing class!"
                raise AvivError(err)
        except AttributeError:
            self.exp_type = exp_type_from_file


    def extractData(self):
        """
        General method that extracts data from aviv file into attributes of
        Aviv instance.  This is controlled by self.data_extract, a
        dictionary that links column names (keys) to attribute names (values).
        For example, {"Samp._Conc.":"concentrations"} will take data in
        "Samp._Conc." column and place it in the self.concentrations attribute.
        """

        # Create attributes in which to store data from columns
        columns_to_extract = self.data_extract.keys()

        # Find start and end of data
        try:
            start = self.file_keys.index("$MDCDA") + 2
            end = self.file_keys.index("$ENDDA")
            data = self.file_contents[start:end]
        except IndexError:
            err = "Problem locating data in file!"
            raise AvivError(err)

        # Grab name of each column in the file
        columns_in_file = self.file_contents[start-1].split()
        column_indexes = dict([(x,i) for i, x in enumerate(columns_in_file)])

        # Look for columns that are supposed to be extracted but aren't found
        for k in columns_to_extract:

            # If the specified column is missing, try to find another name for
            # it in ALTERNATE_COLUMN_KEYS
            if k not in columns_in_file:

                # See if there is another global name for this column
                try:
                    new_key = ALTERNATE_COLUMN_KEYS[k]
                except KeyError:
                    continue

                # If the alternate name for the column is found in the file,
                # rename the key in self.data_extract
                if new_key in columns_in_file:
                    self.data_extract[new_key] = self.data_extract.pop(k)
                    columns_to_extract.remove(k)
                    columns_to_extract.append(new_key)


        # Create attributes of self for each data column to be extracted
        self.__dict__.update([(self.data_extract[c],[])
                              for c in columns_to_extract])
        
        # Extract columns specified in self.data_extract.keys to attributes
        # in self.data_extract.values
        for line in data:
            column = line.split()
            
            for c in columns_to_extract:
                try:
                    attribute = self.data_extract[c]
                    index = column_indexes[c]
                    value = float(column[index])
                    self.__dict__[attribute].append(value)
                except KeyError:
                    print "Warning! Column \"%s\" not found!" % c
                    #raise AvivError(err)
                except ValueError:
                    err = "Problem with \"%s\" column on line:\n%s" % (c,line)
                    raise AvivError(err)


    def extractConfiguration(self):
        """
        Grabs instrument configuration information of interest from data file.
        It does this using self.config_extract list.  This list is made up of
        instances of ConfigureAttribute. 
        """

        tmp_config_extract = [ConfigAttribute("$EXPNAME","name","Name",
                                              str,"%s"),
                              ConfigAttribute("$EXDESC","description",
                                              "Description",str,"%s"),
                              ConfigAttribute("$MDY","date","Date",
                                              str,"%s")]
        self.config_extract = tmp_config_extract + self.config_extract
 
        # Find config data
        config_dict = dict([(c.aviv_key,c) for c in self.config_extract])
        config_start = [l[0:7] for l in self.file_contents].index("$CONFIG") + 1
        config_data = [l.split(":") for l in self.file_contents[config_start:]]
        config_data = [d for d in config_data if d[0] in config_dict.keys()]

        # Append to proper attributes
        for l in config_data:
            attribute = config_dict[l[0]].name
            value_type = config_dict[l[0]].type

            # Strip extra space.  If value has multiple parts (i.e. date), keep
            # as a list.  Otherwise, make a single value.
            values = []
            for v in l[1:]:
                values.append(value_type(v.strip()))
            if len(values) == 1:
                values = values[0]
           
            config_dict[l[0]].value = values
            self.__dict__[attribute] = config_dict[l[0]] 

        # Extract data (special processing)
        self.raw_date = self.date.value
        for i in range(3):
            if len(self.date.value[i]) == 1:
                self.date.value[i] = "0%s" % self.date.value[i]
        
        self.date.value = "%s.%s.%s" % (self.date.value[2],
                                        self.date.value[0],
                                        self.date.value[1])


    def createConfigHeader(self):
        """
        Generate a summary of the instrument configuration that can be placed
        as a header on the final output of the program.
        """

        self.config_out = []

        # Write out instrument configuration data
        fmt = "%s: %s\n"
        self.config_out.append("----- Experiment information -----\n")
        self.config_out.append(fmt % ("Input file",self.input_file))
        self.config_out.append(fmt % ("Instrument",self.instrument))
        self.config_out.append(fmt % ("Experiment",self.exp_type))
        self.config_out.append("\n")

        self.config_out.append("----- Instrument configuration -----\n")
        for c in self.config_extract:
            fmt = "%s: %s\n" % (c.title,c.format)
            self.config_out.append(fmt % c.value)   #self.__dict__[c.name].value)
        self.config_out.append("\n")

        return "".join(self.config_out)


class CD(Aviv):
    """
    Class for parsing CD experiment files.
    """

    instrument_kwargs = [("num_residues",int,"required"),
                         ("molec_weight",float,"required"),
                         ("protein_conc",float,"required"),
                         ("path_length",float,"required")]

    def setupInstrumentExtraction(self,**kwargs):
        """
        Set up data_extract and config_extract to grab information
        relavent to any CD experiment.
        """

        self.num_channels = 1
        self.instrument = "CD"
        self.grab_sample = True
        self.grab_reference = False

        # CD-specific data columns to extract
        self.data_extract["CD_Signal"] = "cd_signal"
        self.data_extract["CD_Error"] = "cd_err"

        # Set self.concentrations to None in case we do not extract it from the
        # data file (e.g. in a temperature melt)
        self.concentrations = None

        # CD-specific configuration options to extract
        self.config_extract.extend([ConfigAttribute("$MONOWL","wavelength",
                                                    "Wavelength",float,"%.3F"),
                                    ConfigAttribute("$MONOBW","bandwidth",
                                                    "Bandwidth",float,"%.3F"),
                                    ConfigAttribute("$TEMPSP",
                                                    "sample_temperature",
                                                    "Sample temperature",
                                                    float,"%.3F")])

        # Grab data from kwargs required for MME conversion
        try:
            self.num_residues = kwargs["num_residues"]
            self.molec_weight = kwargs["molec_weight"]
            self.protein_conc = kwargs["protein_conc"]
            self.path_length = kwargs["path_length"]
        except KeyError:
            err = "num_residues, molec_weight, protein_conc, and path_length keywords are "
            err += "required!"
            raise AvivError(err)



    def grabChannels(self):
        """
        Populate channel_list with Channel instances for further processing.
        """

        self.channel_list = [Channel(name="sample",
                                     x=self.all_x,
                                     y=self.cd_signal,
                                     y_err=self.cd_err,
                                     concentrations=self.concentrations,
                                     shot_size=self.shot_size)]


class ATF(Aviv):
    """
    Class for parsing ATF experiment files.
    """

    instrument_kwargs = [("sample",bool,"required"),
                         ("reference",bool,"required"),
                         ("qc_corr",bool,"optional")]

    def setupInstrumentExtraction(self,**kwargs):
        """
        Set up data_extract and config_extract to grab information
        relavent to any ATF experiment.
        """
   
        self.num_channels = 2
        self.instrument = "ATF"

 
        # ATF specific data columns to extract
        self.data_extract["QC_Signal"] = "qc_signal"
        self.data_extract["PMT_Signal_(Dark)"] = "dark_signal"

        # Set self.concentrations to None in case we do not extract it from the
        # data file (e.g. in a temperature melt)
        self.sample_concentrations = None
        self.reference_concentrations = None

        # ATF specific configuration options to extract
        self.config_extract.extend([ConfigAttribute("$EXWL",
                                                    "excitation_wavelength",
                                                    "Excitation wavelength",
                                                    float, "%.3F"),
                                    ConfigAttribute("$EMWL",
                                                    "emission_wavelength",
                                                   "Emission wavelenth",
                                                   float, "%.3F"),
                                    ConfigAttribute("$EXBW",
                                                    "excitation_bandwidth",
                                                   "Excitation bandwidth",
                                                   float,"%.3F"),
                                    ConfigAttribute("$EMBW",
                                                    "emission_bandwidth",
                                                   "Emission bandwidth",
                                                   float,"%.3F")])


        # --- Deal with channel specific data and configuration options --- #

        # Make sure at least one input is specified (with ex. sample=True)
        self.grab_sample = False
        self.grab_reference = False
        at_least_one_required = ["sample","reference"]
        to_grab = [a for a in at_least_one_required if a in kwargs.keys()]

        if len(to_grab) == 0:
            err = "At least one of the following options is required for "
            err += "%s experiments:\n" % self.instrument
            err += "\n".join(at_least_one_required)
            raise AvivError(err)

        if "sample" in to_grab and kwargs["sample"] == True:
            self.grab_sample = True
            self.config_extract.append(ConfigAttribute("$TEMPSP",
                                                       "sample_temperature",
                                                       "Sample temperature",
                                                       float,"%.3F"))
            self.data_extract["Samp._PMT_Raw_Sig."] = "sample_y"
        
        if "reference" in to_grab and kwargs["reference"] == True:
            self.grab_reference = True
            self.config_extract.append(ConfigAttribute("$TEMPREFSP",
                                                       "ref_temperature",
                                                       "Reference temperature",
                                                       float,"%.3F"))
            self.data_extract["Ref._PMT_Raw_Sig."] = "reference_y"


    def grabChannels(self):
        """
        Populate channel_list with Channel instances for further processing.
        """

        self.channel_list = []

        # If x is not specified individually in the experiment, it will be in
        # the all_x attribute.  If x values are specified for each channel,
        # they should already by in sample_x and reference_x.
        try:
            self.sample_x = self.all_x
            self.reference_x = self.all_x
        except AttributeError:
            pass

        if self.grab_sample:
            try:
                self.channel_list.append(Channel("sample",
                                                 self.sample_x,
                                                 self.sample_y,
                                                 concentrations=
                                                 self.concentrations,
                                                 qc_signal=self.qc_signal,
                                                 dark_signal=self.dark_signal,
                                                 shot_size=self.shot_size))
            except AvivError:
                self.grab_sample = False

        if self.grab_reference:
            try:
                self.channel_list.append(Channel("reference",
                                                 self.reference_x,
                                                 self.reference_y,
                                                 concentrations=
                                                 self.concentrations,
                                                 qc_signal=self.qc_signal,
                                                 dark_signal=self.dark_signal,
                                                 shot_size=self.shot_size))
            except AvivError:
                self.grab_reference = False

        
class Unknown(Aviv):
    """
    Class to deal with an unknown instrument.  Useful for pre-reading file 
    do decide which processing to do.
    """

    def __init__(self,input_file):
        """
        Initialize instance of the class.
        """
        
        self.input_file = input_file
        self.loadFile()


    def identifyExperiment(self):
        """
        Return a tuple of (instrument,exp_type) to allow identification of
        correct parser.
        """

        return (self.instrument,self.exp_type)
    

