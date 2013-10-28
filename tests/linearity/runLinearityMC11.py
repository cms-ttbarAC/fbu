#! /bin/env python

import sys, os
import numpy as np

from fbu.pyFBU import pyFBU
from tests.linearity import computeAc, linearity
from utils import plot

def count_outside_range(elements, hi, lo): return sum(1 for e in elements if e>hi or e<lo)
#__________________________________________________________
if __name__ == "__main__":
    lin_dir = './tests/linearity/'
    pyfbu = pyFBU()
    pyfbu.nMCMC = 100000
    pyfbu.nBurn = 1000
    pyfbu.nThin = 10
    pyfbu.verbose = False
    json_dir = lin_dir+'data/mc11/'
    pyfbu.lower, pyfbu.upper = 70000, 140000
    pyfbu.jsonMig = json_dir+'migrations.json'
    pyfbu.jsonBkg = json_dir+'background.json'

    data_fnames = ["dataA%s%s.json"%(ax, pn) for pn in ['pos','neg'] for ax in [2, 4, 6]]
    meanAc, stdAc = [], []
    TestPassed = True
    for data_fname in data_fnames:
        pyfbu.jsonData  = json_dir+data_fname
        pyfbu.modelName = data_fname.replace('.json','')
        pyfbu.run()
        # np.save('outputFile'+data_fname.replace('.json',''),trace) # un-needed? DG 2013-10-27
        acValues = np.array(computeAc.computeAcList(pyfbu.trace))
        meanAc.append(np.mean(acValues))
        stdAc.append(np.std(acValues))
        plot.plotarray(acValues,'Ac_posterior_'+data_fname.replace('.json',''))
        mean, sigma = np.mean(acValues), np.std(acValues)
        num_outsiders = count_outside_range(acValues, mean+3.*sigma, mean-3.*sigma)
        ratio = float(num_outsiders)/float(len(pyfbu.trace))
        if ratio>0.0027:
            print ("outsiders: %i, ratio  %f"%(num_outsiders, ratio)
                   +'-->> this is NOT ok, should be < 0.0027 (3sigmas)')
            TestPassed = TestPassed and False
    meanAc, stdAc = np.array(meanAc), np.array(stdAc)
    testflag = linearity.dolinearityplot(meanAc, stdAc)

    TestPassed = TestPassed and testflag

    if TestPassed: print 'TEST PASSED'
    else :         print 'TEST FAILED'
