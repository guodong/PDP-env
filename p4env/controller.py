from mininet.node import Controller
from mininet.log import info
import json
import p4env.p4runtime_lib.helper
import p4env.p4runtime_lib.bmv2


# object hook for josn library, use str instead of unicode object
# https://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-from-json
def json_load_byteified(file_handle):
    return _byteify(json.load(file_handle, object_hook=_byteify),
                    ignore_dicts=True)


def _byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


class P4Controller(Controller):
    def __init__(self, name, **kwargs):
        Controller.__init__(self, name, **kwargs)
        self.switches = kwargs['switches']

    def start(self):
        print 'controller start'
        for s in self.switches:
            p4info_helper = p4env.p4runtime_lib.helper.P4InfoHelper(s.p4info)
            conn = p4env.p4runtime_lib.bmv2.Bmv2SwitchConnection(
                name=s.name,
                device_id=s.device_id,
                address='127.0.0.1:%d' % s.grpc_port)
            conn.MasterArbitrationUpdate()
            conn.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                             bmv2_json_file_path=s.pipeline)
            print("Installed P4 Program using SetForwardingPipelineConfig on %s" % s.name)

            # TODO: ugly fix!
            table_entries = _byteify(json.loads(json.dumps(s.table_entries), object_hook=_byteify), ignore_dicts=True)
            info("Inserting %d table entries...\n" % len(table_entries))
            for entry in table_entries:
                info(self.tableEntryToString(entry))
                self.insertTableEntry(conn, entry, p4info_helper)

    def insertTableEntry(self, sw, flow, p4info_helper):
        table_name = flow['table']
        match_fields = flow.get('match')  # None if not found
        action_name = flow['action_name']
        default_action = flow.get('default_action')  # None if not found
        action_params = flow['action_params']
        priority = flow.get('priority')  # None if not found

        table_entry = p4info_helper.buildTableEntry(
            table_name=table_name,
            match_fields=match_fields,
            default_action=default_action,
            action_name=action_name,
            action_params=action_params,
            priority=priority)

        sw.WriteTableEntry(table_entry)

    def tableEntryToString(self, flow):
        if 'match' in flow:
            match_str = ['%s=%s' % (match_name, str(flow['match'][match_name])) for match_name in
                         flow['match']]
            match_str = ', '.join(match_str)
        elif 'default_action' in flow and flow['default_action']:
            match_str = '(default action)'
        else:
            match_str = '(any)'
        params = ['%s=%s' % (param_name, str(flow['action_params'][param_name])) for param_name in
                  flow['action_params']]
        params = ', '.join(params)
        return "%s: %s => %s(%s)\n" % (
            flow['table'], match_str, flow['action_name'], params)
