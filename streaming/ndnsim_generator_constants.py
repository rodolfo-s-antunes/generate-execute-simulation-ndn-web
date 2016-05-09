#!/usr/bin/python

CODEHEADER = '''#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/ndnSIM-module.h"
using namespace ns3;
'''

MAINDEF = '''int
main (int argc, char *argv[]) {
CommandLine cmd;
cmd.Parse (argc, argv);
'''

TOPOLOGYDEF = '''Config::SetDefault ("ns3::PointToPointNetDevice::DataRate", StringValue ("1000Mbps"));
Config::SetDefault ("ns3::PointToPointNetDevice::Mtu", StringValue ("65000"));
Config::SetDefault ("ns3::PointToPointChannel::Delay", StringValue ("5ms"));
Config::SetDefault ("ns3::DropTailQueue::MaxPackets", StringValue ("200"));
AnnotatedTopologyReader topologyReader ("", 25);
topologyReader.SetFileName ("{}"); 
topologyReader.Read ();
'''

NDNDEF = '''ndn::StackHelper ndnHelper;
ndnHelper.SetDefaultRoutes(true);
ndnHelper.SetForwardingStrategy("ns3::ndn::fw::BestRoute");
ndnHelper.SetContentStore("ns3::ndn::cs::Lru", "MaxSize", "{}");
ndnHelper.InstallAll();
ndn::GlobalRoutingHelper ndnGlobalRoutingHelper;
ndnGlobalRoutingHelper.InstallAll();
'''

CODETAIL = '''ndn::GlobalRoutingHelper::CalculateRoutes ();
ndn::CsTracer::InstallAll ("trace/cs-trace-{0}.txt", Seconds (1));
ndn::L3AggregateTracer::InstallAll ("trace/aggregate-trace-{0}.txt", Seconds (1.0));
Simulator::Stop (Seconds ({1}));
Simulator::Run ();
Simulator::Destroy ();
return 0; }}
'''
