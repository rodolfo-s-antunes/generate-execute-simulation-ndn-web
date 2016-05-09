#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, random
import networkx as nx

class PopsWithTrees:
	def __init__(self, topofile):
		self.G = nx.read_gml(topofile)
		self.ir = 0
		self.cr = 0
		self.cn = max(self.G.nodes())+1
		self.popnodes = list(self.G.nodes())
		self.consumernodes = list()
		self.__insertChilds()
		return
	def __insertChilds(self):
		for ipop in self.popnodes:
			self.G.node[ipop]['name'] = str.format('POP{}', ipop)
			self.G.node[ipop]['pop'] = 1
			self.__genChildTree(ipop)
			self.__genChildTree(ipop)
		return
	def __genChildTree(self, pop):
		auxrouter = self.cn
		auxchild1 = self.cn+1
		auxchild2 = self.cn+2
		self.G.add_node(auxrouter, ir=1, name=str.format('IR{}', self.ir))
		self.G.add_node(auxchild1, cr=1, name=str.format('CR{}', self.cr))
		self.G.add_node(auxchild2, cr=1, name=str.format('CR{}', self.cr+1))
		if 'Country' in self.G.node[pop]:
			self.G.node[auxchild1]['Country'] = self.G.node[pop]['Country']
			self.G.node[auxchild2]['Country'] = self.G.node[pop]['Country']
		self.G.add_edge(auxrouter, auxchild2)
		self.G.add_edge(auxrouter, auxchild1)
		self.G.add_edge(pop, auxrouter)
		self.consumernodes.append(auxchild1)
		self.consumernodes.append(auxchild2)
		self.cn += 3
		self.ir += 1
		self.cr += 2
		return
	def SaveNS3(self, savefile):
		arqout = open(savefile, 'w')
		arqout.write('# Routers:\nrouter\n')
		for inode in sorted(self.G.node):
			arqout.write(str.format('{}\tNA\t0.0\t0.0\n', self.G.node[inode]['name']))
		arqout.write('\n# Links:\nlink\n')
		for ilb in sorted(self.G.edge):
			for ile in sorted(self.G.edge[ilb]):
				arqout.write(str.format('{}\t{}\t1000Mbps\t1\t5ms\t200\n', self.G.node[ilb]['name'], self.G.node[ile]['name']))
		arqout.close()
		return

class PopsWithoutTrees:
	def __init__(self, topofile, versionlist=None):
		self.G = nx.read_gml(topofile)
		if versionlist != None:
			self.__insertContentVersions(versionlist)
		self.popnodes = list(self.G.nodes())
		for ipop in self.popnodes:
			self.G.node[ipop]['name'] = str.format('POP{}', ipop)
		self.consumernodes = self.popnodes
		return
	def __insertContentVersions(self, versionlist):
		counter = random.randint(0,len(versionlist)-1)
		for inode in sorted(self.G.node):
			self.G.node[inode]['Country'] = versionlist[counter]
			counter = (counter+1)%len(versionlist)
		return
	def SaveNS3(self, savefile):
		arqout = open(savefile, 'w')
		arqout.write('# Routers:\nrouter\n')
		for inode in sorted(self.G.node):
			arqout.write(str.format('{}\tNA\t0.0\t0.0\n', self.G.node[inode]['name']))
		arqout.write('\n# Links:\nlink\n')
		for ilb in sorted(self.G.edge):
			for ile in sorted(self.G.edge[ilb]):
				arqout.write(str.format('{}\t{}\t1000Mbps\t1\t5ms\t200\n', self.G.node[ilb]['name'], self.G.node[ile]['name']))
		arqout.close()
		return

class PopsSimple:
	def __init__(self):
		self.G = nx.Graph()
		self.G.add_node(0, name='POP0')
		self.G.add_node(1, name='IR0')
		self.G.add_node(2, name='CR0', Country='UK')
		self.G.add_node(3, name='CR1', Country='UK')
		self.G.add_edge(0,1)
		self.G.add_edge(1,2)
		self.G.add_edge(1,3)
		self.popnodes = [0]
		self.consumernodes = [2,3]
		return
	def SaveNS3(self, savefile):
		arqout = open(savefile, 'w')
		arqout.write('# Routers:\nrouter\n')
		for inode in sorted(self.G.node):
			arqout.write(str.format('{}\tNA\t0.0\t0.0\n', self.G.node[inode]['name']))
		arqout.write('\n# Links:\nlink\n')
		for ilb in sorted(self.G.edge):
			for ile in sorted(self.G.edge[ilb]):
				arqout.write(str.format('{}\t{}\t1000Mbps\t1\t5ms\t200\n', self.G.node[ilb]['name'], self.G.node[ile]['name']))
		arqout.close()
		return

class PopsDumbell:
	def __init__(self):
		self.G = nx.Graph()
		self.G.add_node(0, name='PUB')
		self.G.add_node(1, name='POPUK', Country='UK')
		self.G.add_node(2, name='POPES', Country='ES')
		self.G.add_node(3, name='POPNL', Country='NL')
		self.G.add_node(4, name='POPFR', Country='FR')
		self.G.add_node(5, name='POPDE', Country='DE')
		self.G.add_node(6, name='POPIT', Country='IT')
		self.G.add_edge(0,1)
		self.G.add_edge(1,3)
		self.G.add_edge(2,3)
		self.G.add_edge(3,4)
		self.G.add_edge(4,5)
		self.G.add_edge(4,6)
		self.popnodes = [0,1,2,3,4,5,6]
		self.consumernodes = [1,2,3,4,5,6]
		return
	def SaveNS3(self, savefile):
		arqout = open(savefile, 'w')
		arqout.write('# Routers:\nrouter\n')
		for inode in sorted(self.G.node):
			arqout.write(str.format('{}\tNA\t0.0\t0.0\n', self.G.node[inode]['name']))
		arqout.write('\n# Links:\nlink\n')
		for ilb in sorted(self.G.edge):
			for ile in sorted(self.G.edge[ilb]):
				arqout.write(str.format('{}\t{}\t1000Mbps\t1\t5ms\t200\n', self.G.node[ilb]['name'], self.G.node[ile]['name']))
		arqout.close()
		return
