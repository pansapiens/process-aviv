__description__ = """"""
__author__ = "Michael J. Harms"
__date__ = ""

import sys, os
from base import *

class Titration:
    """
    Class with methods to process a titration experiment.
    """

    experiment_kwargs = [("sam_buf",float,"required"),
                         ("sam_titr",float,"required"),
                         ("ref_buf",float,"required"),
                         ("ref_titr",float,"required"),
                         ("init_conc",float,"optional"),
                         ("titrant_conc",float,"optional"),
                         ("cell_vol",float,"optional")]

    def setupExperimentExtraction(self,**kwargs):
        """
        Method to decide which configuration options and data columns to
        grab for any titration experiment.
        """

        self.exp_type = "Titration"

        # Experiment-specific configuration options to extract.
        self.config_extract.extend([ConfigAttribute("$CONCSYRTITRANT",
                                                    "titrant_conc",
                                                    "Titrant concentration",
                                                    float,"%.3F"),
                                    ConfigAttribute("$CONCINITTITRANT",
                                                    "init_conc",
                                                    "Initial titrant",
                                                    float,"%.3F"),
                                    ConfigAttribute("$CONCCELLVOL",
                                                    "cell_vol",
                                                    "Cuvette volume",
                                                    float,"%.3F"),
                                    ConfigAttribute("$CONCTARGET2",
                                                    "final_titr_conc",
                                                    "Final [titrant]",
                                                    float,"%.3F")])
      
        # Extract experiment-specific data columns 
        self.data_extract["X"] = "all_x"
        self.data_extract["Samp._Conc."] = "concentrations"
        self.data_extract["Inj._Vol._ul."] = "shot_size" 


    def processChannels(self,**kwargs):
        """
        Process data by correcting for buffer and titrant blanks, converting 
        to MME (if this is a CD experiment), then normalizing.
        """

        # Make sure that buffer and titrant blanks are specified for each
        # channel.
        kwarg_keys = kwargs.keys()
        blank_dict = {}
        if self.grab_sample:
            try:
                blank_dict["sample"] = (kwargs["sam_buf"],kwargs["sam_titr"])
            except KeyError:
                err = "sam_buf and sam_titr blank values must be specified!\n"
                raise AvivError(err)
            
        if self.grab_reference:
            try:
                blank_dict["reference"] = (kwargs["ref_buf"],kwargs["ref_titr"])
            except KeyError:
                err = "ref_buf and ref_titr blank values must be specified!\n"
                raise AvivError(err)
        
        # Grab passed kwargs relevant to denaturant correction 
        corr_denat_keys = ["init_conc","titrant_conc","cell_vol"]
        denat_corr_kwargs = dict([(k,kwargs[k]) for k in kwargs.keys()
                                  if k in corr_denat_keys])

        process_log = []
        for c in self.channel_list:

            process_log.append("----- %s channel processing -----\n" % 
                               c.name.capitalize())

            # Correct denaturant concentration, if requested
            if len(denat_corr_kwargs) != 0:
                instrument_values = [self.init_conc,
                                     self.titrant_conc,
                                     self.cell_vol]
                process_log.append(c.correctDenaturant(instrument_values,
                                                       **denat_corr_kwargs))

            # Correct for the quantum counter, if requested
            if self.instrument == "ATF":
                try:
                    if kwargs["qc_corr"] == True:
                        process_log.append(c.correctDarkQC())
                except KeyError:
                    pass
            
            # Correct for titrant blanks
            process_log.append(c.correctTitrantBlanks(*blank_dict[c.name]))
          
            # Correct for dilution 
            process_log.append(c.correctDilution())
                
            # Convert to MME and normalize
            if self.instrument == "CD":
                process_log.append(c.convertToMME(self.num_residues,
                                                  self.molec_weight,
                                                  self.protein_conc,
                                                  self.path_length))
                process_log.append(c.normalizeSignal(invert=True))
            else:
                process_log.append(c.normalizeSignal())

            process_log.append("\n")

        return "".join(process_log)       

    def createOutput(self,column_width=12):
        """
        Create R-readable output that can then be used for fitting.
        """

        # Create some format strings
        int_width = "%" + ("%ii" % column_width)
        str_width = "%" + ("%is" % column_width)
        float_width = "%" + ("%i.3F" % column_width)

        # Figure out which columns to take and what to call them
        if self.instrument == "CD":
            to_write = ["x","raw_signal","raw_err","norm_signal",
                        "norm_err","MME","MME_err"]
            header = ["x","raw","raw_err","norm","norm_err","MME","MME_err"]

        else:
            to_write = ["x","raw_signal","norm_signal"]
            header = ["x","raw","norm"]

        # Create header
        out = []
        if self.grab_sample:
            out.extend(["s_%s" % c for c in header])
        if self.grab_reference:
            out.extend(["r_%s" % c for c in header])
        out.insert(0," ")
        out = [str_width % c for c in out]
        out.append("\n")

        # Place proper channel attributes into list for output
        out_list = []
        for c in self.channel_list:
            for w in to_write:
                out_list.append(c.__dict__[w])

        # Create output
        num_columns = len(out_list)
        num_rows = len(out_list[0])
        for i in range(num_rows):
            out.append(int_width % i)
            for j in range(num_columns):
                out.append(float_width % out_list[j][i])
            out.append("\n")

        return "".join(out)  


class pH:
    """
    Class with methods to process a pH titration experiment.
    """

    def setupExperimentExtraction(self,**kwargs):
        """
        Method to decide which configuration options and data columns to
        grab for any pH experiment.
        """

        self.exp_type = "pH"
      
        # Extract experiment-specific data columns 
        self.data_extract["pH_Inj._Volumes"] = "shot_size"
        self.data_extract["Samp._Conc."] = "concentrations"

        # Grab independent pH channels for the ATF
        if self.instrument == "ATF":
            try:
                if kwargs["sample"] == True:
                    self.data_extract["pH_Channel_1"] = "sample_x"
            except KeyError:
                pass

            try:
                if kwargs["reference"] == True:
                    self.data_extract["pH_Channel_2"] = "reference_x"
            except KeyError:
                pass

        # Grab a single channel for the CD
        else:
            self.data_extract["X"] = "all_x"


    def processChannels(self,**kwargs):
        """
        Process data by correcting for dilution, converting 
        to MME (if this is a CD experiment), then normalizing.
        """

        process_log = []
        for c in self.channel_list:

            process_log.append("----- %s channel processing -----\n" % 
                               c.name.capitalize())

            # Correct for the quantum counter, if requested
            if self.instrument == "ATF":
                try:
                    if kwargs["qc_corr"] == True:
                        process_log.append(c.correctDarkQC())
                except KeyError:
                    pass

            # Correct for dilution
            process_log.append(c.correctDilution())
 
            # Convert to MME and normalize
            if self.instrument == "CD":
                process_log.append(c.convertToMME(self.num_residues,
                                                  self.molec_weight,
                                                  self.protein_conc,
                                                  self.path_length))
                process_log.append(c.normalizeSignal(invert=True))
            else:
                process_log.append(c.normalizeSignal())

            process_log.append("\n")

        return "".join(process_log)       

    def createOutput(self,column_width=12):
        """
        Create R-readable output that can then be used for fitting.
        """

        # Create some format strings
        int_width = "%" + ("%ii" % column_width)
        str_width = "%" + ("%is" % column_width)
        float_width = "%" + ("%i.3F" % column_width)

        # Figure out which columns to take and what to call them
        if self.instrument == "CD":
            to_write = ["x","raw_signal","raw_err","norm_signal",
                        "norm_err","MME","MME_err"]
            header = ["pH","raw","raw_err","norm","norm_err","MME","MME_err"]

        else:
            to_write = ["x","raw_signal","norm_signal"]
            header = ["pH","raw","norm"]

        # Create header
        out = []
        if self.grab_sample:
            out.extend(["s_%s" % c for c in header])
        if self.grab_reference:
            out.extend(["r_%s" % c for c in header])
        out.insert(0," ")
        out = [str_width % c for c in out]
        out.append("\n")

        # Place proper channel attributes into list for output
        out_list = []
        for c in self.channel_list:
            for w in to_write:
                out_list.append(c.__dict__[w])

        # Create output
        num_columns = len(out_list)
        num_rows = len(out_list[0])
        for i in range(num_rows):
            out.append(int_width % i)
            for j in range(num_columns):
                out.append(float_width % out_list[j][i])
            out.append("\n")

        return "".join(out)  


class Temperature:
    """
    Class with methods to process a temperature melt experiment.
    """

    def setupExperimentExtraction(self,**kwargs):
        """
        Method to decide which configuration options and data columns to
        grab for any pH experiment.
        """

        self.exp_type = "Temperature"
      
        # Grab independent temperature channels for the ATF
        if self.instrument == "ATF":
            try:
                if kwargs["sample"] == True:
                    self.data_extract["Sample_Temp"] = "sample_x"
                    self.config_extract = [c for c in self.config_extract
                                           if c.aviv_key != "$TEMPSP"]
            except KeyError:
                pass

            try:
                if kwargs["reference"] == True:
                    self.data_extract["Reference_Temp"] = "reference_x"
                    self.config_extract = [c for c in self.config_extract
                                           if c.aviv_key != "$TEMPREFSP"]
            except KeyError:
                pass

        # Grab a single channel for the CD
        else:
            self.data_extract["X"] = "all_x"
            self.config_extract = [c for c in self.config_extract
                                   if c.aviv_key != "$TEMPSP"]


    def processChannels(self,**kwargs):
        """
        Process data by converting to MME (if this is a CD experiment), then
        normalizing.
        """

        process_log = []
        for c in self.channel_list:

            process_log.append("----- %s channel processing -----\n" % 
                               c.name.capitalize())

            # Correct for the quantum counter, if requested
            if self.instrument == "ATF":
                try:
                    if kwargs["qc_corr"] == True:
                        process_log.append(c.correctDarkQC())
                except KeyError:
                    pass

            # Convert to MME and normalize
            if self.instrument == "CD":
                process_log.append(c.convertToMME(self.num_residues,
                                                  self.molec_weight,
                                                  self.protein_conc,
                                                  self.path_length))
                process_log.append(c.normalizeSignal(invert=True))
            else:
                process_log.append(c.normalizeSignal())

            process_log.append("\n")

        return "".join(process_log)       

    def createOutput(self,column_width=12):
        """
        Create R-readable output that can then be used for fitting.
        """

        # Create some format strings
        int_width = "%" + ("%ii" % column_width)
        str_width = "%" + ("%is" % column_width)
        float_width = "%" + ("%i.3F" % column_width)

        # Figure out which columns to take and what to call them
        if self.instrument == "CD":
            to_write = ["x","raw_signal","raw_err","norm_signal",
                        "norm_err","MME","MME_err"]
            header = ["temp","raw","raw_err","norm","norm_err","MME","MME_err"]

        else:
            to_write = ["x","raw_signal","norm_signal"]
            header = ["temp","raw","norm"]

        # Create header
        out = []
        if self.grab_sample:
            out.extend(["s_%s" % c for c in header])
        if self.grab_reference:
            out.extend(["r_%s" % c for c in header])
        out.insert(0," ")
        out = [str_width % c for c in out]
        out.append("\n")

        # Place proper channel attributes into list for output
        out_list = []
        for c in self.channel_list:
            for w in to_write:
                out_list.append(c.__dict__[w])

        # Create output
        num_columns = len(out_list)
        num_rows = len(out_list[0])
        for i in range(num_rows):
            out.append(int_width % i)
            for j in range(num_columns):
                out.append(float_width % out_list[j][i])
            out.append("\n")

        return "".join(out)  


class Wavelength:
    """
    Class with methods to process a CD wavelength experiment.
    """

    experiment_kwargs = [("blank_file",str,"optional")]
    
    def setupExperimentExtraction(self,**kwargs):
        """
        Method to decide which configuration options and data columns to
        grab for a wavelength experiment.
        """

        self.exp_type = "Wavelength"
      
        if self.instrument == "ATF":
            err = "Script cannot be used to process ATF wavelength experiments!"
            raise AvivError(err)

        self.data_extract["X"] = "all_x"


    def processChannels(self,**kwargs):
        """
        Process data by removing blank and converting to MME.
        """

        try:
            blank_file = kwargs["blank_file"]
        except KeyError:
            blank_file = None

        process_log = []
        for c in self.channel_list:

            process_log.append("----- %s channel processing -----\n" % 
                               c.name.capitalize())

            # Remove blank and convert to MME
            process_log.append(c.subtractBlank(blank_file))
            process_log.append(c.convertToMME(self.num_residues,
                                              self.molec_weight,
                                              self.protein_conc,
                                              self.path_length))
            process_log.append("\n")

        return "".join(process_log)       


    def createOutput(self,column_width=12):
        """
        Create R-readable output that can then be used for plotting.
        """

        # Create some format strings
        int_width = "%" + ("%ii" % column_width)
        str_width = "%" + ("%is" % column_width)
        float_width = "%" + ("%i.3F" % column_width)

        # Figure out which columns to take and what to call them
        to_write = ["x","raw_signal","raw_err","MME","MME_err"]
        header = ["wavelength","raw","raw_err","MME","MME_err"]

        # Create header
        out = []
        if self.grab_sample:
            out.extend(["s_%s" % c for c in header])
        if self.grab_reference:
            out.extend(["r_%s" % c for c in header])
        out.insert(0," ")
        out = [str_width % c for c in out]
        out.append("\n")

        # Place proper channel attributes into list for output
        out_list = []
        for c in self.channel_list:
            for w in to_write:
                out_list.append(c.__dict__[w])

        # Create output
        num_columns = len(out_list)
        num_rows = len(out_list[0])
        for i in range(num_rows):
            out.append(int_width % i)
            for j in range(num_columns):
                out.append(float_width % out_list[j][i])
            out.append("\n")

        return "".join(out)  
