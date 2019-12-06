from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.topo import Topo
from mininet.log import info
from p4env.controller import P4Controller
from itertools import groupby
import os
import json
import time
from p4env.p4switch import P4Switch
from cmd import Cmd


class NetworkTopo(Topo):

    def __init__(self, topo_file, **opts):
        Topo.__init__(self, **opts)
        with open(topo_file, 'r') as f:
            topo = json.load(f)
            self.topo = topo

        for sw, params in topo['switches'].items():
            p4info_path = os.path.dirname(os.path.abspath(topo_file)) + '/' + params['p4info']
            pipeline_path = os.path.dirname(os.path.abspath(topo_file)) + '/' + params['pipeline']
            self.addSwitch(sw, cls=P4Switch, sw_path=params['exe'], p4info=p4info_path,
                           pipeline=pipeline_path, table_entries=params['table_entries'])

        for h, params in topo['hosts'].items():
            self.addHost(h, ip=params['ip'], mac=params['mac'])

        for l in topo['links']:
            self.addLink(l[0], l[1])


class MininetRunner:
    def __init__(self, topo_file):
        topo = NetworkTopo(topo_file)
        self.net = Mininet(topo=topo, controller=None)
        self.net.addController(controller=P4Controller, switches=self.net.switches)

        self.start()
        time.sleep(1)

        """ Execute any commands provided in the topology.json file on each Mininet host
                """
        for host_name, host_info in topo.topo['hosts'].items():
            h = self.net.get(host_name)
            if "commands" in host_info:
                for cmd in host_info["commands"]:
                    h.cmd(cmd)

        self.net.staticArp()

        CLI(self.net)
        # stop right after the CLI is exited
        self.net.stop()

    def start(self):
        "Start controller and switches."
        if not self.net.built:
            self.net.build()
        info('*** Starting %s switches\n' % len(self.net.switches))
        for switch in self.net.switches:
            info(switch.name + ' ')
            switch.start(self.net.controllers)
        started = {}
        for swclass, switches in groupby(
                sorted(self.net.switches,
                       key=lambda s: str(type(s))), type):
            switches = tuple(switches)
            if hasattr(swclass, 'batchStartup'):
                success = swclass.batchStartup(switches)
                started.update({s: s for s in success})
        info('\n')
        info('*** Starting controller\n')
        for controller in self.net.controllers:
            info(controller.name + ' ')
            controller.start()
        info('\n')
        if self.net.waitConn:
            self.net.waitConnected()


class CmdLine(Cmd):
    intro = 'Welcome to the PDP-env shell.   Type help or ? to list commands.\n'
    prompt = 'PDP-env> '

    def __init__(self):
        Cmd.__init__(self)

    def do_start_network(self, line):
        if line == '':
            print 'please input topo file path'
            return
        if not os.path.exists(line):
            print 'cannot find topo file'
            return
        MininetRunner(line)

    def do_clean_mininet(self, line):
        os.system('sudo mn -c')

    def do_exit(self, line):
        return True


if __name__ == '__main__':
    setLogLevel("info")
    c = CmdLine()
    c.cmdloop()
