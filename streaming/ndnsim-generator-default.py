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
		self.__getLocations(T)
		self.producers = random.sample(self.consumers, pn)
		for ip in self.producers:
			self.consumers.pop(ip)
		return
	def __getLocations(self, T):
		self.countries = ['Default']
		for ic in T.consumernodes:
			name = T.G.node[ic]['name']
			country = 'None'
			if 'Country' in T.G.node[ic]:
				country = removeSpaces(T.G.node[ic]['Country'])
			if country not in self.countries: self.countries.append(country)
			self.consumers[name]['country'] = country
		return

class ConfGenerator:
	def __init__(self, nodes, P):
		self.nodes = nodes
		self.P = P
		self.P['chunkmax'] = int(self.P['audiochunkmax']) + int(self.P['videochunkmax'])
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
		self.__writeProducer()
		self.arqout.write('\n')
		self.__writeConsumers()
		self.arqout.write('\n')
		self.__writeCodeTail()
		self.arqout.close()
		return
	def __writeTopology(self):
		self.arqout.write(str.format(TOPOLOGYDEF, 'scratch/'+self.P['topoout']))
		return
	def __writeRandomSeed(self):
		self.arqout.write(str.format("RngSeedManager::SetSeed ({});\n", self.P['seed']))
		return
	def __calcCacheSize(self):
		cachesize = float(self.P['cachesize'])
		nocache = int(self.P['nocache'])
		if nocache > 0:
			return 1
		elif not cachesize > 0:
			return 0
		else:
			countrynumber = float(len(self.nodes.countries))
			chunkmax = int(self.P['audiochunkmax']) + int(self.P['videochunkmax'])
			totalcontent = chunkmax*float(self.P['catalogsize'])*countrynumber
			auxv = int(totalcontent*cachesize)
			if auxv < 1: return 1
			else: return auxv
		return
	def __writeNdn(self):
		self.arqout.write(str.format(NDNDEF, self.__calcCacheSize()))
		#self.arqout.write(str.format(NDNDEF, int(self.P['cachesize'])))
		return
	def __writeCodeTail(self):
		self.arqout.write(str.format(CODETAIL, self.P['name'], self.P['simulationtime']))
		return
	def __writeProducer(self):
		count = 0
		for ip in self.nodes.producers:
			self.arqout.write(str.format('Ptr<Node> producer{} = Names::Find<Node> ("{}");\n', count, ip))
			self.arqout.write(str.format('ndn::AppHelper producerHelper{} ("ns3::ndn::Producer");\n', count))
			self.arqout.write(str.format('producerHelper{}.SetPrefix("/ufrgs");\n', count))
			self.arqout.write(str.format('ndnGlobalRoutingHelper.AddOrigins ("/ufrgs", producer{});\n', count))
			self.arqout.write(str.format('producerHelper{}.SetAttribute("PayloadSize", StringValue("{}"));\n', count, self.P['chunksize']))
			self.arqout.write(str.format('producerHelper{}.SetAttribute("NodeName", StringValue("{}"));\n', count, ip))
			self.arqout.write(str.format('producerHelper{}.Install (producer{});\n', count, count))
			count += 1
		return
	def __writeConsumers(self):
		self.arqout.write('NodeContainer consumerNodes;\n')
		clc = 0
		for ic in sorted(self.nodes.consumers):
			consumer = self.nodes.consumers[ic]
			self.arqout.write(str.format('consumerNodes.Add (Names::Find<Node>("{}"));\n', ic))
			self.arqout.write(str.format('ndn::AppHelper consumerHelper{} ("ns3::ndn::ConsumerRsa");\n', clc))
			self.arqout.write(str.format('consumerHelper{}.SetPrefix ("/ufrgs");\n', clc))
			self.arqout.write(str.format('consumerHelper{}.SetAttribute ("ClientName", StringValue ("{}"));\n', clc, ic))
			self.arqout.write(str.format('consumerHelper{}.SetAttribute ("ArrivalMean", DoubleValue ({}));\n', clc, self.P['arrivalmean']))
			self.arqout.write(str.format('consumerHelper{}.SetAttribute ("ChunkInterval", DoubleValue ({}));\n', clc, self.P['chunkinterval']))
			self.arqout.write(str.format('consumerHelper{}.SetAttribute ("RelSufix", StringValue ("{}"));\n', clc, consumer['country']))
			self.arqout.write(str.format('consumerHelper{}.SetAttribute ("HasSepAudio", BooleanValue (false));\n', clc))
			self.arqout.write(str.format('consumerHelper{}.SetAttribute ("SizeVideo", UintegerValue ({}));\n', clc, self.P['chunkmax']))
			self.arqout.write(str.format('consumerHelper{}.SetAttribute ("NumberOfContents", UintegerValue ({}));\n', clc, self.P['catalogsize']))
			self.arqout.write(str.format('consumerHelper{}.SetAttribute ("q", DoubleValue ({}));\n', clc, self.P['zipfmandq']))
			self.arqout.write(str.format('consumerHelper{}.SetAttribute ("s", DoubleValue ({}));\n', clc, self.P['zipfmands']))
			self.arqout.write(str.format('consumerHelper{}.Install (consumerNodes[{}]);\n', clc, clc))
			clc += 1
		return

class Main:
	def __init__(self):
		P = self.__defaultParms()
		self.__parseArgs(P)
		random.seed(int(P['seed']))
		versionlist = ['UK', 'IT', 'ES', 'DE', 'FR']
		#versionlist = ['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'v16', 'v17', 'v18', 'v19', 'v20']
		P['versionquant'] = len(versionlist)
		if int(P['toposimple']) == 1:
			topology = PopsDumbell()
			topology.SaveNS3(P['topoout'])
		else:
			topology = PopsWithoutTrees('topologias/'+P['topoin'], versionlist)
			topology.SaveNS3(P['topoout'])
		ng = NodeGenerator(topology, int(P['numpublishers']))
		cg = ConfGenerator(ng, P)
		cg.generateFile()
		return
	def __defaultParms(self):
		P = dict()
		P['name'] = 'teste'
		P['seed'] = 1000
		P['cachesize'] = 0.01
		P['nocache'] = 0
		P['catalogsize'] = 10000
		P['simulationtime'] = 4800
		P['chunksize'] = 15000 # Remember the simplification!
		P['arrivalmean'] = '1000.0'
		P['chunkinterval'] = '5'
		P['videochunkmax'] = 24
		P['audiochunkmax'] = 1
		P['zipfmands'] = 1.0
		P['zipfmandq'] = 0.0
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
