__description__ = """"""
__author__ = "Michael J. Harms"
__date__ = ""

import base, experiments, instruments
from base import AvivError

class ATF_Titration(base.Parser,instruments.ATF,experiments.Titration):
    """
    Processes an ATF Titration experiment.
    """

    pass

class CD_Titration(base.Parser,instruments.CD,experiments.Titration):
    """
    Processes a CD Titration experiment.
    """

    pass

class ATF_pH(base.Parser,instruments.ATF,experiments.pH):
    """
    Processes an ATF pH experiment.
    """

    pass

class CD_pH(base.Parser,instruments.CD,experiments.pH):
    """
    Processes a CD pH experiment.
    """

    pass


class ATF_Temperature(base.Parser,instruments.ATF,experiments.Temperature):
    """
    Processes an ATF Temperature experiment.
    """

    pass

class CD_Temperature(base.Parser,instruments.CD,experiments.Temperature):
    """
    Processes a CD Temperature experiment.
    """

    pass

class CD_Wavelength(base.Parser,instruments.CD,experiments.Wavelength):

    """
    Processes a CD wavelength scan experiment.
    """

    pass

available_parsers = {("ATF","Titration"):  ATF_Titration,
                     ("CD" ,"Titration"):  CD_Titration,
                     ("ATF","pH"):         ATF_pH,
                     ("CD" ,"pH"):         CD_pH,
                     ("ATF","Temperature"):ATF_Temperature,
                     ("CD" ,"Temperature"):CD_Temperature,
                     ("CD" ,"Wavelength"): CD_Wavelength}


def preParse(input_file):
    """
    
    """
    
    # Create a dummy_parser
    exp_id = instruments.Unknown(input_file).identifyExperiment()
    dummy_parser = available_parsers[exp_id]()
    dummy_parser.exp_id = exp_id
 
    # Make up values for required keywords for this parser, then parse file.
    # This allows extraction of instrument parameters, etc. prior to user input.
    kwarg_dict = dummy_parser.experiment_kwargs[:]
    kwarg_dict.extend(dummy_parser.instrument_kwargs)
    kwarg_dict = [(k[0],k[1](1)) for k in kwarg_dict if k[2] == "required"]
    kwarg_dict = dict(kwarg_dict)

    # Do parsing and return experiment object
    dummy_parser.processFile(input_file=input_file,**kwarg_dict)
    
    
    
    return dummy_parser



#import sys

#yo(sys.argv[1])

#tmp_exp = instruments.Unknown(sys.argv[1])
#print tmp_exp.basicConfiguration()
#exp_id = identifyExperiment(sys.argv[1])
#parser = available_parsers[exp_id]

#exp = parser()
#exp.processFile(input_file=sys.argv[1],num_residues=143,molec_weight=16000,initial_conc=50.,sam_buf=.0,sam_titr=0.0,sample=True,reference=True,ref_buf=0.1,ref_titr=0.2,qc_corr=True,titrant_conc=7)



