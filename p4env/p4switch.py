from mininet.node import Switch
from mininet.moduledeps import pathCheck
from mininet.log import info, error, debug
import psutil
import os, tempfile, time

SWITCH_START_TIMEOUT = 10 # seconds

class P4Switch(Switch):
    "BMv2 switch with gRPC support"
    next_grpc_port = 50051
    next_thrift_port = 9090
    next_device_id = 0

    def __init__(self, name, sw_path=None, grpc_port=None, thrift_port=None, cpu_port=None, p4info=None, pipeline=None, table_entries=[], **kwargs):
        Switch.__init__(self, name, **kwargs)
        assert sw_path
        self.sw_path = sw_path
        # make sure that the provided sw_path is valid
        pathCheck(sw_path)

        self.p4info = p4info
        self.pipeline = pipeline
        self.table_entries = table_entries

        if grpc_port is not None:
            self.grpc_port = grpc_port
        else:
            self.grpc_port = P4Switch.next_grpc_port
            P4Switch.next_grpc_port += 1

        if thrift_port is not None:
            self.thrift_port = thrift_port
        else:
            self.thrift_port = P4Switch.next_thrift_port
            P4Switch.next_thrift_port += 1

        if self.check_listening_on_port(self.grpc_port):
            error('%s cannot bind port %d because it is bound by another process\n' % (self.name, self.grpc_port))
            exit(1)

        self.device_id = P4Switch.next_device_id
        P4Switch.next_device_id += 1
        self.cpu_port = cpu_port

    def check_listening_on_port(self, port):
        for c in psutil.net_connections(kind='inet'):
            if c.status == 'LISTEN' and c.laddr[1] == port:
                return True
        return False

    def check_switch_started(self, pid):
        for _ in range(SWITCH_START_TIMEOUT * 2):
            if not os.path.exists(os.path.join("/proc", str(pid))):
                return False
            if self.check_listening_on_port(self.grpc_port):
                return True
            time.sleep(0.5)

    def start(self, controllers):
        info("Starting P4 switch {}.\n".format(self.name))
        args = [self.sw_path]
        for port, intf in self.intfs.items():
            if not intf.IP():
                args.extend(['-i', str(port) + "@" + intf.name])
        args.extend(['--device-id', str(self.device_id)])

        # we use p4runtime to set pipeline config
        args.append("--no-p4")

        if self.thrift_port:
            args.append('--thrift-port ' + str(self.thrift_port))
        if self.grpc_port:
            args.append("-- --grpc-server-addr 0.0.0.0:" + str(self.grpc_port))
        if self.cpu_port:
            args.append("--cpu-port " + str(self.cpu_port))
        cmd = ' '.join(args)
        info(cmd + "\n")

        pid = None
        with tempfile.NamedTemporaryFile() as f:
            cmd_str = cmd + ' > /dev/null 2>&1 & echo $! >> ' + f.name
            self.cmd(cmd_str)
            pid = int(f.read())
        debug("P4 switch {} PID is {}.\n".format(self.name, pid))
        if not self.check_switch_started(pid):
            error("P4 switch {} did not start correctly.\n".format(self.name))
            exit(1)
        info("P4 switch {} has been started.\n".format(self.name))
