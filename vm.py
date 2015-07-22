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
import os

class VM(object):
    def __init__(self, vm_dict, iso_dir, work_dir, br_names):
        self.name = vm_dict['name']
        self.version = vm_dict['version']
        self.start_port = vm_dict['port_list']['start_port']
        self.end_port = vm_dict['port_list']['end_port']
        self.connections = []
        self.disk = ''
        self.cdrom = ''
        self.extra_commands = {}

        for i in xrange((self.end_port+1-self.start_port)):
            self.connections.append(br_names['dummy'])

        self.connections.insert(0,br_names['mgmt'])
    
        if 'boot_device' in vm_dict.keys():
            self.extra_commands['boot_device'] = vm_dict['boot_device']

        if 'machine_type' in vm_dict.keys():
            self.extra_commands['machine_type'] = vm_dict['machine_type']

        if 'cpu_type' in vm_dict.keys():
            self.extra_commands['cpu_type'] =''
       
        self.console = vm_dict['console']
        
        if os.path.exists(os.path.join(iso_dir,self.version+'.iso')):
            self.cdrom = os.path.join(iso_dir, self.version+'.iso')
        else:
            raise ValueError("ISO not present for %s" % self.name)

        if os.path.exists(os.path.join(iso_dir,self.version+'.vmdk')):
            subprocess.call(['cp', \
            os.path.join(iso_dir, self.version+'.vmdk'), work_dir])
            self.disk = os.path.join(work_dir, self.version+'.vmdk')
        
    def fill_connection(self, endpoint, conn_name, br_names):
        if not endpoint['port'] in \
        xrange(self.start_port, self.end_port+1):
            raise ValueError("Invalid port number for %s in connections"\
            % endpoint['name'])

        if self.connections[endpoint['port']-self.start_port+1] == \
        br_names['dummy']:
            self.connections[endpoint['port']-self.start_port+1]=conn_name
        else:
            raise ValueError("Port %d already used in %s", \
            endpoint['port'], self.name)
