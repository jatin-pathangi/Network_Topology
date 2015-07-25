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

def cleanup():
    data = []
    try:
        f = open('conf/resources.json','r')
        try:
            data = json.load(f)
        except:
            f.close()
            os.remove('conf/resources.json')
            sys.exit(0)
        f.close()
    except IOError:
        print ('Nothing to clean')
        sys.exit(0)
    
    mod_br = nw_topo_bridge
    mod_hyp = nw_topo_hypervisor

    for dic in data:
        if 'COMMON' in dic.keys():
            mod_hyp = getattr(mod_hyp, dic['COMMON']['HYPERVISOR_TYPE'])
            mod_br = getattr(mod_br,dic['COMMON']['BRIDGE_TYPE'])
    
    hyp = mod_hyp()
    for dic in data:
        
        if 'VMs' in dic.keys(): 
            hyp.destroy_vms(dic['VMs'])

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

def console(name):
    data = []
    try:
        f = open('conf/resources.json','r')
        data = json.load(f)
        f.close()
    except IOError:
        print ("Resources file not present. Run main.py with start")
        return
    
    namespace = ''

    for dic in data:
        if 'NAMESPACE' in dic.keys():
            namespace = dic['NAMESPACE']
    
    for dic in data:    
        if 'VMs' in dic.keys():
            for vm in dic['VMs']:
                """
                Add namespace to the name specified because the VMs have 
                been created with
                a namespace appended
                """
                if vm.keys()[0] == name+namespace:
                    if not vm[name+namespace] == 'vnc':
                        subprocess.call(['telnet', 'localhost',\
                        vm[name+namespace]])
                    else:
                        subprocess.call(['virt-viewer', name+namespace])

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
    br_names = {'mgmt':"mgmt", 'dummy':"dummy"}
    
    """
    Make the list of valid bridges and hypervisors by looking at all the 
    subclasses declared of the particular base class.
    """
    for obj in nw_topo_bridge.Bridge.__subclasses__():
        bridge_list.append(obj.__name__)

    for obj in nw_topo_hypervisor.Hypervisor.__subclasses__():
        hypervisor_list.append(obj.__name__)

    brdige_type = hypervisor_type = ''
    namespace = str(os.getpid())
    
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
        
    vm_obj_dict = {}
    
    """
    Add namespace to bridges dummy and mgmt
    """
    for key in br_names:
        br_names[key] = br_names[key]+namespace
   
    """
    Namespace added for VMs
    """
    for vm in vm_list:
        vm['name'] = vm['name'] + namespace
        vm_obj_dict[vm['name']] = (VM(vm,iso_dir,work_dir, br_names))
    
    f = open('conf/resources.json', 'w')

    writable = []
    writable.append({"COMMON":{"BRIDGE_TYPE":bridge_type,\
                    "HYPERVISOR_TYPE":hypervisor_type}})

    writable.append({'bridges':[]})
    writable[1]['bridges'].extend([br_names['mgmt'], \
    br_names['dummy']])
    
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
         
        writable[1]['bridges'].append({key:connections[key]}) 

    """
    Import the hypervisor which is specified in the config file
    """
    HyperVisor = nw_topo_hypervisor
    HyperVisor = getattr(HyperVisor, hypervisor_type)

    hyp = HyperVisor()
    
    """
    Import the bridge which is specified in the config file using getattr
    """
    mod = nw_topo_bridge
    mod = getattr(mod,bridge_type)
    
    mgmt = mod(br_names['mgmt'])
    dummy = mod(br_names['dummy'])
    mgmt.add_bridge()
    dummy.add_bridge()
   
    for key in connections:
        mod(key).add_bridge()
    
    hyp.start_networks(connections, bridge_type, br_names)
    
    vm_obj_list = [vm_obj_dict[key] for key in vm_obj_dict]
    
    writable.append({"VMs":[]})
    for vm in vm_obj_list:
        writable[2]['VMs'].append(hyp.create_vm(vm, work_dir, iso_dir))
    
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

cons.add_argument('name',help="Name of VM to connect to")

root_dir = os.getcwd()
args = parser.parse_args()
if args.directory:
    root_dir = args.directory

os.chdir(root_dir)

if args.which == 'create':
    main()
elif args.which == 'clean':
    cleanup()
elif args.which == 'console':
    console(args.name)
