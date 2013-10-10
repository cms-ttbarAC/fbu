import commands
import json
import os

import pymc as mc
from numpy import array,mean,std, empty, empty_like, random

import matplotlib.pyplot as plt
from pylab import savefig
from pymc.Matplot import plot


class pyFBU(object):
    """A class to perform a MCMC sampling.

    [more detailed description should be added here]

    All configurable parameters are set to some default value, which
    can be changed later on, but before calling the `run` method.
    """
    #__________________________________________________________
    def __init__(self):
        self.nMCMC = 100000 # N trials        [begin MCMC parameters]
        self.nBurn = 1000   # todo: describe
        self.nThin = 10     # todo: describe
        self.lower = 1000   # lower sampling bound
        self.upper = 1500   # upper sampling bound
        #                                     [begin numerical parameters]
        self.projectDir = os.path.dirname(os.path.abspath(__file__)).replace('/python','')
        self.dataDir  = self.projectDir+'/data/'
        self.jsonData = self.dataDir+'data.json'       # json data file
        self.jsonMig  = self.dataDir+'migrations.json' # json migration matrix file
        self.jsonBkg  = self.dataDir+'background.json' # json background file
        self.rndseed  = -1
        self.mcmc     = None # clarify these attributes (better names? required by pymc?)
        self.stats    = None
        self.trace    = None
        self.verbose = False
    #__________________________________________________________
    def asString(self, value) : return str(value)

    #__________________________________________________________
    def fluctuate(self, data):
        random.seed(self.rndseed)
        return random.poisson(data)

    #__________________________________________________________
    def getBackground(self, jsonfname='', variation='Nominal') :
        """Read bkg from json file.
        """
        print "this function will become obsolete; specify bkg values rather than fname"
        nameBkg1 = 'BG'
        valuesBkg1 = json.load(open(jsonfname))[nameBkg1][variation]
        return { 'background1' : valuesBkg1 }

    #__________________________________________________________
    def run(self):
        data = array(json.load(open(self.jsonData)))
        data = self.fluctuate(data) if self.rndseed>=0 else data
        bkgd = self.getBackground(self.jsonBkg) if self.jsonBkg else None
        nreco = len(data)
        migrations = array(json.load(open(self.jsonMig)))
        truth = mc.DiscreteUniform('truth',
                                   lower=self.lower, upper=self.upper,
                                   doc='truth', size=nreco)
        #This is where the FBU method is actually implemented
        @mc.deterministic(plot=False)
        def unfold(truth=truth):
            out = empty(nreco)
            for r in xrange(nreco):
                tmp = 0.0 + sum([bkgd[b][r] for b in bkgd.keys()]) if bkgd else 0.0
                for t in xrange(nreco):
                    tmp += truth[t]*migrations[r][t]
                    out[r:r+1] = tmp
            return out

        #This is the unfolded distribution
        unfolded = mc.Poisson('unfolded', mu=unfold, value=data, observed=True, size=nreco)

        # Define the model using the model class
        model = mc.Model([unfolded, unfold, truth])

        # Call MAP before MCMC to find good starting MCMC values
        map_ = mc.MAP( model )
        map_.fit()


        #Define the MCMC model
        self.mcmc = mc.MCMC( model )
        self.mcmc.use_step_method(mc.AdaptiveMetropolis, truth)
        self.mcmc.sample(self.nMCMC,burn=self.nBurn,thin=self.nThin)
        self.stats = self.mcmc.stats()
        self.trace = self.mcmc.trace("truth")[:]

        plot(self.mcmc)
        savefig("pyfbu_summary.eps")
