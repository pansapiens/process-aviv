#!/usr/bin/env python
"""
denaturantModule.py

Calculate denaturant concentrations given refractive indexes using the Pace
polynomial.  [Pace, CN. (1986). Methods in Enzymology, 131. 266-280]
"""

__author__ = "Michael J. Harms"
__date__ = "070830"
__usage__ = "denaturantModule.py gdn|urea background_n sample_n"

import os, sys

class DenaturantError(Exception):
    """
    General error class for this module.
    """
    
    pass

def calcGdnConc(background_n,sample_n):
    """
    Calculate Gdn concentration.

    """
    
    dn = sample_n - background_n
    return 57.147*dn + 38.68*(dn**2) - 91.60*(dn**3)


def calcUreaConc(background_n,sample_n):
    """
    Calculate urea concentration.
    """
    
    dn = sample_n - background_n
    return 117.66*dn + 29.753*(dn**2) + 185.56*(dn**3)

def calcDenaturantConc(denaturant,background_n,sample_n):
    """
    Calculate a denaturant concentration given the denaturant, background
    refractive index, and sample refractive index.
    """
    
    # Lists of equivalent denaturant names
    gdn_synonyms = ["gdn","gdnhcl","gdm","gdmhcl","g"]
    urea_synonyms = ["urea","u"]
    
    # Perform calculation
    if denaturant.lower() in gdn_synonyms:
        return calcGdnConc(background_n,sample_n)
    elif denaturant.lower() in urea_synonyms:
        return calcUreaConc(background_n,sample_n)
    else:
        err = "Denaturant \"%s\" not recognized!" % denaturant
        raise DenaturantError(err)

def main():
    """
    Function to run if called from the command line.
    """
    
    try:
        denaturant = sys.argv[1]
        background_n = float(sys.argv[2])
        sample_n = float(sys.argv[3])
    except IndexError:
        print __usage__
        sys.exit()
    except ValueError:
        print __usage__
        sys.exit()

    print "%.4F M %s" % (calcDenaturantConc(denaturant,background_n,sample_n),
                         denaturant)
    

# If program called from the command line, run main
if __name__ == "__main__":
    main()
