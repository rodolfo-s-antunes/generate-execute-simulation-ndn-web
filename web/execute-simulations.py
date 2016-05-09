#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, time
import subprocess as subp
from threading import Thread, Semaphore
import numpy as np
import scipy as sp
import scipy.stats as sps
# Módulo com funções para o processamento dos dados de log
# from parse_output import *

BASEDIR = '/home/rsantunes/ndnSIM/ns-3'
CODEDIR = BASEDIR+'/scratch'
TRACEDIR = BASEDIR+'/trace'
BINDIR = BASEDIR+'/build/scratch'
LIBDIR = BASEDIR+'/build'
MYDIR = os.getcwd()
NUMTHREADS = 3
CONFVAL = 0.95
THREADSEM = Semaphore(NUMTHREADS)

class ExecSimulation(Thread):
	def __init__(self, parms, name, storedir):
		Thread.__init__(self)
		self.parms = parms
		self.name = name
		self.storedir = storedir
		if self.storedir not in os.listdir('.'):
			os.mkdir(self.storedir)
		if 'raw' not in os.listdir('./'+self.storedir):
			os.mkdir(self.storedir+'/raw')
		return
	def run(self):
		self.__runSimulation()
		self.__collectResults()
		THREADSEM.release()
		return
	def genConfig(self):
		arqbase = 'simulacao-' + self.name
		self.arqbase = arqbase
		cmdline = str.format('python {0} {1} simout={2}.cc topoout={2}.txt', self.parms['genconfscript'], self.name, arqbase)
		for kp in self.parms:
			if kp not in ['genconfscript']:
				cmdline += str.format(' {}={}', kp, self.parms[kp])
		os.system(cmdline)
		if arqbase+'.cc' in os.listdir(CODEDIR):
			os.unlink(str.format('{}/{}.cc', CODEDIR, arqbase))
		os.symlink(str.format('{}/{}.cc', MYDIR, arqbase), str.format('{}/{}.cc', CODEDIR, arqbase))
		if arqbase+'.txt' in os.listdir(CODEDIR):
			os.unlink(str.format('{}/{}.txt', CODEDIR, arqbase))
		os.symlink(str.format('{}/{}.txt', MYDIR, arqbase), str.format('{}/{}.txt', CODEDIR, arqbase))
		return
	def __runSimulation(self):
		cmdline = BINDIR + '/' + self.arqbase
		procenv = {'LD_LIBRARY_PATH': LIBDIR}
		print str.format('{}: EXEC {}...', time.ctime(), self.name)
		outarq = open(self.storedir+'/raw/out-'+self.name, 'w')
		errarq = open(self.storedir+'/raw/err-'+self.name, 'w')
		proc = subp.Popen(cmdline, cwd=BASEDIR, env=procenv, shell=True, stdout=outarq, stderr=errarq)
		proc.wait()
		print str.format('{}: FINISH {}...', time.ctime(), self.name)
		outarq.close()
		errarq.close()
		return
	def __collectResults(self):
		cmdline = str.format('mv {0}/aggregate-trace-{2}.txt {1}/raw/traffic-{2}.txt', TRACEDIR, self.storedir, self.name)
		os.system(cmdline)
		cmdline = str.format('mv {0}/cs-trace-{2}.txt {1}/raw/cache-{2}.txt', TRACEDIR, self.storedir, self.name)
		os.system(cmdline)
		cmdline = str.format('mv simulacao-{1}.cc {0}/raw/config-{1}.cc', self.storedir, self.name)
		os.system(cmdline)
		cmdline = str.format('mv simulacao-{1}.txt {0}/raw/topologia-{1}.txt', self.storedir, self.name)
		os.system(cmdline)
		os.unlink(str.format('{}/{}.cc', CODEDIR, self.arqbase))
		os.unlink(str.format('{}/{}.txt', CODEDIR, self.arqbase))
		return

class ExecutionControl:
	def __init__(self, simulationruns, storedir):
		self.sr = simulationruns
		self.sd = storedir
		self.tp = list()
		return
	def prepareThreads(self):
		print 'Preparing Execution...'
		for ks in self.sr:
			seedruns = self.sr[ks]
			for ps in seedruns:
				auxthread = ExecSimulation(seedruns[ps], ps, self.sd)
				auxthread.genConfig()
				self.tp.append(auxthread)
		simcomp = subp.Popen('./waf', cwd=BASEDIR, shell=True)
		simcomp.wait()
		return
	def runThreads(self):
		for it in self.tp:
	 		THREADSEM.acquire()
			it.start()
		return
	def joinThreads(self):
		for it in self.tp:
			it.join()
		return

class SimulationRuns:
	def __init__(self):
		self.pdict = dict()
		return
	def addRuns(self, parms, casename, seed, genconfscript):
		runname = str.format('{}_seed:{}', casename, seed)
		auxdict = dict()
		auxdict[runname] = dict(seed=seed, genconfscript=genconfscript)
		for pk in sorted(parms):
			if pk != 'seed':
				vlist = parms[pk]
				newdict = dict()
				for ak in auxdict:
					for vi in vlist:
						runname = ak + str.format('_{}:{}', pk, vi)
						newdict[runname] = dict(auxdict[ak])
						newdict[runname][pk] = vi
				auxdict = newdict
		if int(seed) not in self.pdict:
			self.pdict[int(seed)] = dict()
		for adk in auxdict:
			self.pdict[int(seed)][adk] = auxdict[adk]
		return
	def getRuns(self):
		return self.pdict

class ParseConfig:
	def __init__(self, confarq):
		self.ca = confarq
		self.cd = None
		self.sl = None
		return
	def getSeedList(self):
		if self.sl == None:
			self.__getConfig()
		return self.sl
	def getConfig(self):
		if self.cd == None:
			self.__getConfig()
		return self.cd
	def __getConfig(self):
		self.cd = dict()
		arq = open(self.ca, 'r')
		for linha in arq:
			auxQ = linha.strip().split('=')
			parm = auxQ[0].strip()
			auxV = auxQ[1].strip().split(';')
			if parm == 'seed':
				self.sl = [x.strip() for x in auxV]
			else:
				self.cd[parm] = [x.strip() for x in auxV]
		arq.close()
		return

class Main():
	def __init__(self):
		if len(sys.argv) != 3:
			print str.format('Usage: {} <config.conf> <resultdir>', sys.argv[0])
			sys.exit(1)
		conffile = sys.argv[1]
		resultdir = sys.argv[2]
		pc = ParseConfig(conffile)
		sr = SimulationRuns()
		for seed in pc.getSeedList():
			sr.addRuns(pc.getConfig(), 'default', seed, 'ndnsim-generator-default.py')
			sr.addRuns(pc.getConfig(), 'relations', seed, 'ndnsim-generator-relations.py')
		ec = ExecutionControl(sr.getRuns(), resultdir)
		ec.prepareThreads()
		ec.runThreads()
		ec.joinThreads()
		return

if __name__ == '__main__':
	Main()
