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

from abc import ABCMeta, abstractmethod
import os
import socket
import subprocess 
import json
import sys

class Hypervisor(object):
    """
    Hypervisor class from which all sub hypervisor classes inherit their
    methods.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def start_networks(self, *args, **kwargs):
        #Method to start the network bridges specified in the arguments.
        pass

    @abstractmethod
    def create_vm(self, *args, **kwargs):
        #Method to start vm from the VM object in the arguments.
        pass

    @abstractmethod
    def destroy_networks(self, *args, **kwargs):
        #Method to destroy networks created. Uses a resources file for this.
        pass

    @abstractmethod
    def destroy_restart_stop_vms(self, *args, **kwargs):
        #Method to kill all VMs created. Uses a resources file for this.
        pass

"""
Class that starts networks and VMs and also destroys them in KVM
"""
class KVM(Hypervisor):
    telnet_start_port = 20000  #Default port to start using for console
    def __init__(self):
        pass
    
    """
    Function to generate the file that is used by virsh net commands to
    start the networks
    """
    def gen_net_xml(self, sw_name, br_typ):
        f_obj = open('conf/net.xml', 'w')

        f_obj.write('<network>\n')
        
        f_obj.write("\t<name>%s</name>\n" % sw_name)
        f_obj.write("\t<forward mode = 'bridge'/>\n")
        f_obj.write("\t<bridge name = '%s'/>\n" % sw_name)
        
        #Linux Bridge does not require virtualport type to be written in
        if br_typ == 'OVSBridge':
            f_obj.write("\t<virtualport type = 'openvswitch'/>\n")
    
        f_obj.write("</network>\n")
        f_obj.close()

    
    """
    Function that calls the virsh net commands after creating XML files for
    each network.
    """
    def start_networks(self, connections, br_type, br_names):
        """
        Bridges list can be used to create the bridges using
        subprocess.call()
        """
        bridges = []
        bridges.extend([br_names['mgmt'], br_names['dummy']])
        bridges.extend(connections.keys())
        
        print bridges
        for i in xrange(len(bridges)):
            com0 = 'virsh'
            com1 = '--connect'
            com2 = 'qemu:///system'
            
            self.gen_net_xml(bridges[i], br_type)
            subprocess.call([com0,com1,com2,'net-define', 'conf/net.xml'])
            subprocess.call([com0,com1,com2,'net-autostart', bridges[i]])
            subprocess.call([com0,com1,com2,'net-start', bridges[i]])
        
        os.remove('conf/net.xml')

    """
    Function to get an empty TCP port in case the VM is to be connected via
    telnet. To connect to the VM's console via telnet, the port returned
    by this function is used
    """
    def get_port(self):
        start_port = KVM.telnet_start_port
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('', start_port))
            except socket.error as msg:
                start_port += 10
                sock.close()
                continue
            sock.close()
            KVM.telnet_start_port = start_port + 1
            return start_port
     
    """
    Function to add the --network set of commands to the virt install 
    commands
    """
    def add_network(self, cmd_list, vm):
        for i in vm.connections:
            cmd_list.append('--network')
            cmd_list.append('network=%s,model=e1000' \
            % i)
        
        return cmd_list
    
    """
    Function to start the VMs using virt-install commands
    """
    def create_vm(self, vm, work_dir, iso_dir):
        name_to_port = {}
        form = ''
        extra = []
        
        if not vm.disk == '':
            form = os.path.splitext(vm.disk)[1]
            form = form[1:]
        else:
            form = 'qcow2'
            subprocess.call(['qemu-img', 'create', '-fqcow2',\
            os.path.join(work_dir,(vm.name+'.img')), '16G'])

            vm.disk = os.path.join(work_dir,vm.name+'.img')
    
        cmd_list = [
        'virt-install', 
         '--name=%s' % vm.name, 
         '--ram=1024', 
         '--disk=%s,format=%s,device=disk,bus=ide' % (vm.disk,form), 
         '--cdrom='+os.path.join(iso_dir,(vm.version+'.iso')),
         '--watchdog','i6300esb,action=none']

        if 'boot_device' in vm.extra_commands.keys():
            if vm.extra_commands['boot_device'] == 'cdrom':
                cmd_list.append('--livecd')

        if 'machine_type' in vm.extra_commands.keys():
            cmd_list.append('--machine='+vm.extra_commands['machine_type'])

        if 'cpu_type' in vm.extra_commands.keys():
            cmd_list.extend(['--cpu', 'qemu64,disable=svm'])

        if vm.console == "telnet":
            tcp_port = self.get_port()
            cmd_list.extend(['--graphics', 'none', '--serial',\
            'tcp,host=:%d,mode=bind,protocol=telnet' % tcp_port\
            ,'--noautoconsole'])
            name_to_port[vm.name] = "%d" % tcp_port            
        else:
            cmd_list.extend(['--graphics', 'vnc', '--noautoconsole'])
            name_to_port[vm.name] = "vnc"
        
        cmd_list = self.add_network(cmd_list, vm)

        subprocess.call(cmd_list)

        return name_to_port

    def destroy_networks(self,bridge):
        com0 = 'virsh'
        com1 = '--connect'
        com2 = 'qemu:///system'
        
        subprocess.call([com0,com1,com2,'net-destroy', bridge])
        subprocess.call([com0,com1,com2,'net-undefine',bridge])

        
    def destroy_restart_stop_vms(self, vms, restart_or_stop):
        for vm in vms:
            subprocess.call(['virsh','destroy', vm.keys()[0]])
            if restart_or_stop == 'clean':
                subprocess.call(['virsh','undefine',vm.keys()[0]])
            elif restart_or_stop == 'restart':
                subprocess.call(['virsh', 'start', vm.keys()[0]])
            elif restart_or_stop == 'stop':
                pass
            else:
                print ("Illegal argument to destroy_restart_stop_vms. Should be\
                        'clean', 'restart' or 'stop'")
