#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, math, random, bisect
import networkx as nx
import numpy as np
# O módulo abaixo contém os blocos de código constantes utilizados na
# configuração da simulação. Deixei eles em um arquivo serparado
# para não gerar poluição neste arquivo.
from ndnsim_generator_constants import *
# O módulo abaixo contém o código para geração de topologias de POPs
# aumentadas com árvores de 2 níveis (metodologia do artigo do Shenker)
from include_tree_topology import *

def removeSpaces(linha):
	result = ''
	for c in linha:
		if c != ' ':
			result += c
	return result

class NodeGenerator:
	def __init__(self, T, pn):
		self.consumers = {T.G.node[x]['name']:dict() for x in T.consumernodes}
		self.producers = random.sample(self.consumers, pn)
		return

def CalcCatalogSize(P):
	mf = sorted([float(P['datasize']), float(P['layoutsize']), float(P['codesize'])])
	result = 0.0
	with open(P['sizetracefile'], 'r') as arq:
		for L in arq:
			base = float(L.strip())
			aux = base
			aux += math.ceil(base*(mf[1]/mf[0]))
			aux += math.ceil(base*(mf[2]/mf[0]))
			result += aux
	return result

class ConfGenerator:
	def __init__(self, nodes, P):
		self.nodes = nodes
		self.P = P
		return
	def generateFile(self):
		self.arqout = open(self.P['simout'], 'w')
		self.arqout.write(CODEHEADER)
		self.arqout.write('\n')
		self.arqout.write(MAINDEF)
		self.arqout.write('\n')
		self.__writeRandomSeed()
		self.arqout.write('\n')
		self.__writeTopology()
		self.arqout.write('\n')
		self.__writeNdn()
		self.arqout.write('\n')
		self.__writeVersionControl()
		self.arqout.write('\n')
		self.__writeProducer()
		self.arqout.write('\n')
		self.__writeConsumers()
		self.arqout.write('\n')
		self.__writeCodeTail()
		self.arqout.close()
		return
	def __writeTopology(self):
		self.arqout.write(TOPOLOGYDEF.format('scratch/'+self.P['topoout']))
		return
	def __writeRandomSeed(self):
		self.arqout.write("RngSeedManager::SetSeed ({});\n".format(self.P['seed']))
		return
	def __calcCacheSize(self):
		cachesize = float(self.P['cachesize'])
		nocache = int(self.P['nocache'])
		if nocache:
			return 0
		elif not cachesize < 1:
			return cachesize
		else:
			totalcontent = CalcCatalogSize(self.P)
			auxv = totalcontent*cachesize
			if auxv < 1: return 1
			else: return int(auxv)
		return
	def __writeNdn(self):
		self.arqout.write(NDNDEF.format(self.__calcCacheSize()))
		#self.arqout.write(str.format(NDNDEF, int(self.P['cachesize'])))
		return
	def __writeVersionControl(self):
		self.arqout.write('Ptr<WebVersionControl> wbc = Create<WebVersionControl>(true);\n')
		self.arqout.write('wbc->readSizeTrace("scratch/{}");\n'.format(self.P['sizetracefile']))
		self.arqout.write('wbc->insertAll({}, {}, {}, {}, {}, {}, {});\n'.format(self.P['catalogsize'], self.P['dataupfreq'], self.P['layoutupfreq'], self.P['codeupfreq'], self.P['datasize'], self.P['layoutsize'], self.P['codesize']))
		return
	def __writeCodeTail(self):
		self.arqout.write(CODETAIL.format(self.P['name'], self.P['simulationtime']))
		return
	def __writeProducer(self):
		count = 0
		for ip in self.nodes.producers:
			self.arqout.write('Ptr<Node> producer{} = Names::Find<Node> ("{}");\n'.format(count, ip))
			self.arqout.write('ndn::AppHelper producerHelper{} ("ns3::ndn::ProducerRSAWeb");\n'.format(count))
			self.arqout.write('producerHelper{}.SetPrefix("/ufrgs");\n'.format(count))
			self.arqout.write('ndnGlobalRoutingHelper.AddOrigins ("/ufrgs", producer{});\n'.format(count))
			self.arqout.write('producerHelper{}.SetAttribute("PayloadSize", StringValue("{}"));\n'.format(count, self.P['chunksize']))
			self.arqout.write('producerHelper{}.SetAttribute("UpdateInterval", DoubleValue({}));\n'.format(count, self.P['updateinterval']))
			self.arqout.write('producerHelper{}.SetAttribute("VersionControl", PointerValue(wbc));\n'.format(count))
			self.arqout.write('producerHelper{}.Install (producer{});\n'.format(count, count))
			count += 1
		return
	def __writeConsumers(self):
		self.arqout.write('NodeContainer consumerNodes;\n')
		clc = 0
		for ic in sorted(self.nodes.consumers):
			consumer = self.nodes.consumers[ic]
			self.arqout.write('consumerNodes.Add (Names::Find<Node>("{}"));\n'.format(ic))
			self.arqout.write('ndn::AppHelper consumerHelper{} ("ns3::ndn::ConsumerRSAWeb");\n'.format(clc))
			self.arqout.write('consumerHelper{}.SetPrefix ("/ufrgs");\n'.format(clc))
			self.arqout.write('consumerHelper{}.SetAttribute ("ClientName", StringValue ("{}"));\n'.format(clc, ic))
			self.arqout.write('consumerHelper{}.SetAttribute ("ArrivalMean", DoubleValue ({}));\n'.format(clc, self.P['arrivalmean']))
			self.arqout.write('consumerHelper{}.SetAttribute ("ChunkInterval", DoubleValue ({}));\n'.format(clc, self.P['chunkinterval']))
			self.arqout.write('consumerHelper{}.SetAttribute("UsingRelations", BooleanValue(true));\n'.format(clc))
			self.arqout.write('consumerHelper{}.SetAttribute ("NumberOfContents", UintegerValue ({}));\n'.format(clc, self.P['catalogsize']))
			self.arqout.write('consumerHelper{}.SetAttribute ("q", DoubleValue ({}));\n'.format(clc, self.P['zipfmandq']))
			self.arqout.write('consumerHelper{}.SetAttribute ("s", DoubleValue ({}));\n'.format(clc, self.P['zipfmands']))
			self.arqout.write('consumerHelper{}.SetAttribute("VersionControl", PointerValue(wbc));\n'.format(clc))
			self.arqout.write('consumerHelper{}.Install (consumerNodes[{}]);\n'.format(clc, clc))
			clc += 1
		return

class Main:
	def __init__(self):
		P = self.__defaultParms()
		self.__parseArgs(P)
		random.seed(int(P['seed']))
		if int(P['toposimple']) == 1:
			topology = PopsDumbell()
			topology.SaveNS3(P['topoout'])
		else:
			topology = PopsWithoutTrees('topologias/'+P['topoin'])
			topology.SaveNS3(P['topoout'])
		ng = NodeGenerator(topology, int(P['numpublishers']))
		cg = ConfGenerator(ng, P)
		cg.generateFile()
		return
	def __defaultParms(self):
		P = dict()
		# General parameters
		P['name'] = 'teste'
		P['seed'] = 1000
		P['cachesize'] = 0.1
		P['nocache'] = False
		P['simulationtime'] = 300
		# Client behavior
		P['arrivalmean'] = 2000
		P['chunkinterval'] = 10
		# Content
		P['catalogsize'] = 10000
		P['chunksize'] = 1000
		P['updateinterval'] = 100
		P['dataupfreq'] = 0.8696
		P['layoutupfreq'] = 0.0 # 0.0435
		P['codeupfreq'] = 0.0 # 0.0541
		P['sizetracefile'] = 'tracesizes.txt'
		P['datasize'] = 0.65
		P['layoutsize'] = 0.15
		P['codesize'] = 0.2
		P['zipfmands'] = 1.0
		P['zipfmandq'] = 0.0
		# Topology
		P['numpublishers'] = 1
		P['toposimple'] = 0
		P['simout'] = 'simulacao.cc'
		P['topoout'] = 'simulacao.txt'
		P['topoin'] = 'BtLA.gml'
		return P
	def __parseArgs(self, parms):
		parms['name'] = sys.argv[1]
		for arg in sys.argv[2:]:
			Q = arg.split('=')
			parms[Q[0]] = Q[1]
		return

if __name__ == '__main__':
	Main()
