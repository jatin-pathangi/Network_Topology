#!/usr/bin/env python
"""

   Copyright 2015 Jatinshravan

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import subprocess
import json
from vm import VM
import argparse
import nw_topo_bridge 
import nw_topo_hypervisor
import os
import sys

def get_class(mod, data, typ):
    for dic in data:
        if 'COMMON' in dic.keys():
            mod = getattr(mod, dic['COMMON'][typ])
            break

    return mod

def cleanup(data):
    mod_br = nw_topo_bridge
    mod_hyp = nw_topo_hypervisor
    hypervisor_type = None
    hypervisor_data = None
    
    mod_br = get_class(mod_br, data, 'BRIDGE_TYPE')
    mod_hyp = get_class(mod_hyp, data, 'HYPERVISOR_TYPE')

    for dic in data:
        if 'COMMON' in dic.keys():
            hypervisor_type = dic['COMMON']['HYPERVISOR_TYPE']

    for dic in data:
        if hypervisor_type in dic.keys():
            hypervisor_data = dic[hypervisor_type]


    hyp = mod_hyp(hypervisor_data)
    for dic in data:
        
        if 'VMs' in dic.keys(): 
            hyp.destroy_restart_stop_vms(dic['VMs'], 'clean')

    for dic in data:
        if 'bridges' in dic.keys():
            for item in dic['bridges']:
                destroyable = ''
                """
                There are two types in the list of values of the bridge
                key in the resources.json file. mgmt and dummy are strings
                whereas others are dictionaries
                """
                if type(item).__name__ == 'dict':
                    destroyable = item.keys()[0]
                else:
                    destroyable = item

                hyp.destroy_networks(destroyable)
                mod_br(destroyable).del_bridge()

    for i in os.listdir('working_dir'):
        os.remove(os.path.join('working_dir',i))

    os.remove('conf/resources.json')

def console(data, name):
    namespace = ''

    for dic in data:
        if 'NAMESPACE' in dic.keys():
            namespace = dic['NAMESPACE']
    
    for dic in data:    
        if 'VMs' in dic.keys():
            for vm in dic['VMs']:
                if vm.keys()[0] == name+namespace:
                    if not vm[name+namespace] == 'vnc':
                        subprocess.call(['telnet', 'localhost',\
                        vm[name+namespace]])
                    else:
                        subprocess.call(['virt-viewer', name+namespace])

def restart_or_stop(data,name, _all, stop):
    flag = False
    destroyable = ''
    namespace = ''

    for dic in data:
        if 'NAMESPACE' in dic.keys():
            namespace = dic['NAMESPACE']

    for dic in data:
        if 'VMs' in dic.keys():
            for vm in dic['VMs']:
                if _all:
                    destroyable = vm.keys()[0]
                    flag = True

                else:
                    if vm.keys()[0] == name+namespace:
                        destroyable = name+namespace
                        flag = True
                    
                    else:
                        continue
                
                subprocess.call(['virsh','destroy',str(destroyable)])
                if not stop:
                    subprocess.call(['virsh','start',str(destroyable)])

                if not _all and flag:
                    break

    if not flag:
        print ("Invalid VM name, not present in created VM list")
    
def main():
    work_dir = "working_dir"
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    if os.path.exists('conf/resources.json'):
        print ("Please run main.py with clean argument once")
        return -1

    iso_dir = ""
    data = []
    try:
        f = open('conf/config.json','r')
        data = json.load(f)
        f.close()

    except IOError:
        print ("Config file 'conf/config.json' not present")
        return -1

    bridge_list = hypervisor_list = []
    vm_list = []
    connections = {}
    brdige_type = hypervisor_type = ''
    hypervisor_data = None
    namespace = str(os.getpid())
    
    br_names = {'mgmt':"mgmt", 'dummy':"dummy"}
    
    """
    Make the list of valid bridges and hypervisors by looking at all the 
    subclasses declared of the particular base class.
    """
    for obj in nw_topo_bridge.Bridge.__subclasses__():
        bridge_list.append(obj.__name__)

    for obj in nw_topo_hypervisor.Hypervisor.__subclasses__():
        hypervisor_list.append(obj.__name__)

    for dic in data:
        if 'COMMON' in dic.keys():
            """
            Check if a bridge is specified in the config file. If not, 
            use OpenVSwitch as default.
            """
            if 'BRIDGE' in dic['COMMON'].keys(): 
                bridge_type = dic['COMMON']['BRIDGE'] 
                if not bridge_type in bridge_list:
                    print ("Invalid bridge %s, list of valid \
                    bridges are:" % bridge_type)
                    for i in bridge_list:
                        print (i)
            else:
                bridge_type = 'OVSBridge'

            if 'ISO_DIR' in dic['COMMON'].keys():
                iso_dir = dic['COMMON']['ISO_DIR']
            else:
                print ("iso directory not specified in config file")
                return -1

            if 'HYPERVISOR' in dic['COMMON'].keys():
                hypervisor_type = dic['COMMON']['HYPERVISOR']
                if not hypervisor_type in hypervisor_list:
                    print ("Invalid Hypervisor %s, list of valid \
                    hypervisors are:" % hypervisor_type )
                    for i in hypervisor_list:
                        print (i)
            
            else:
                hypervisor_type = 'KVM'

            if 'NAMESPACE' in dic['COMMON'].keys():
                namespace = dic['COMMON']['NAMESPACE']
        
        if 'VMS' in dic.keys():
            vm_list = dic['VMS']

        if 'CONNECTIONS' in dic.keys():
            connections = dic['CONNECTIONS']

        if 'BRIDGE_NAMES' in dic.keys():
            br_names = dic["BRIDGE_NAMES"]

        if hypervisor_type in dic.keys():
            hypervisor_data = dic[hypervisor_type]

    vm_obj_dict = {}
    
    """
    Add namespace to bridges dummy and mgmt
    """
    for key in br_names:
        br_names[key] = br_names[key]+namespace

    """
    Import the hypervisor which is specified in the config file
    """
    HyperVisor = nw_topo_hypervisor
    HyperVisor = getattr(HyperVisor, hypervisor_type)

    hyp = HyperVisor(hypervisor_data)
    
    """
    Import the bridge which is specified in the config file using getattr
    """
    mod = nw_topo_bridge
    mod = getattr(mod,bridge_type)
    
    mgmt = mod(br_names['mgmt'])
    dummy = mod(br_names['dummy'])

    for vm in vm_list:
        vm['name'] = vm['name'] + namespace
        vm_obj_dict[vm['name']] = (VM(vm,iso_dir,work_dir, br_names))
    
    f = open('conf/resources.json', 'w')

    writable = []
    writable.append({'bridges':[]})
    writable.append({"VMs":[]})
    writable[0]['bridges'].extend([br_names['mgmt'], \
    br_names['dummy']])
    writable.append({"COMMON":{"BRIDGE_TYPE":bridge_type,\
                    "HYPERVISOR_TYPE":hypervisor_type}})

    writable.append({hypervisor_type:hypervisor_data})
    
    namespace_conn = {}
    for key in connections:
        namespace_conn[key+namespace] = connections[key]
        
    connections = namespace_conn
    
    for key in connections:
        conn_name = key
        for endp in connections[key]:
            endp['name'] = endp['name']+namespace
            if endp['name'] in vm_obj_dict.keys():
                vm_obj_dict[endp['name']].fill_connection\
                (endp,conn_name, br_names)
            else:
                raise ValueError("Connection name %s not present in valid\
                VM list" % endp['name'])
         
        writable[0]['bridges'].append({key:connections[key]}) 

    mgmt.add_bridge()
    dummy.add_bridge()
   
    for key in connections:
        mod(key).add_bridge()
    
    hyp.start_networks(connections, bridge_type, br_names)
    
    vm_obj_list = [vm_obj_dict[key] for key in vm_obj_dict]
    
    for vm in vm_obj_list:
        writable[1]['VMs'].append(hyp.create_vm(vm, work_dir, iso_dir))
    
    writable.append({'NAMESPACE':namespace})
    json.dump(writable,f)
    f.close()

parser = argparse.ArgumentParser(prog=sys.argv[0])
parser.add_argument('-d', '--directory', help="Directory for config file")
parser.add_argument('--version', action='version', version='%(prog)s 0.5')
subparser = parser.add_subparsers(help="Help for subcommand", dest='which')

start = subparser.add_parser('create',help="Create VMs and netwroks")
clean=subparser.add_parser('clean',help="Destroy VMs and networks created")
cons=subparser.add_parser('console', help="Connect to VM console")
rest = subparser.add_parser('restart',help="Restart VM")
stop = subparser.add_parser('stop',help="Stop VM")

cons.add_argument('name',help="Name of VM to connect to")
rest.add_argument('name',nargs='?',default='',help="Name of VM to restart")
rest.add_argument('--all', action='store_true', help="Restart all VMs")
stop.add_argument('name',nargs='?',default='',help="Name of VM to restart")
stop.add_argument('--all', action='store_true', help="Restart all VMs")

root_dir = os.getcwd()
args = parser.parse_args()
if args.directory:
    root_dir = args.directory

os.chdir(root_dir)

if args.which == 'create':
    main()
    sys.exit(0)

data = []
try:
    f = open('conf/resources.json','r')
    data = json.load(f)
    f.close()
except IOError:
    sys.stdout.write("No resources created. Run with create option")

if args.which == 'clean':
    cleanup(data)
elif args.which == 'console':
    console(data,args.name)
if args.which == 'restart' or args.which == 'stop':
    if args.all and not args.name == '':
        print ("Give either the name of a VM or --all")
    
    else:
        if args.which == 'restart':
            restart_or_stop(data, args.name, args.all, False)
        if args.which == 'stop':
            restart_or_stop(data, args.name,args.all, True)
