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
    def __init__(self, hyp_params):
        #Method to initialize the hypervisor
        pass

    @abstractmethod
    def start_networks(self, connections, br_type, br_name): 
        #Method to start the network bridges specified in the arguments.
        pass

    @abstractmethod
    def create_vm(self, vm, work_dir, iso_dir):
        #Method to start vm from the VM object in the arguments.
        pass

    @abstractmethod
    def destroy_networks(self, bridge):
        #Method to destroy networks created. Uses a resources file for this.
        pass

    @abstractmethod
    def destroy_restart_stop_vms(self, vms, action):
        #Method to kill all VMs created. Uses a resources file for this.
        pass

"""
Class that handle ESXI hypervisor
"""
class ESXI(Hypervisor):
    def __init__(self, hyp_params):
        if ((hyp_params != None) and ("datastore" in hyp_params)):
            if (os.path.isdir(hyp_params["datastore"])):
                self.datast = hyp_params["datastore"]
            else:
                print ('not able to access data store ',hyp_params["datastore"])
                sys.exit(1)
        else:
            print ("Required parameter - datastore missing for ESXI hypervisor")
            sys.exit(1)
        print ("In ESXI INit", self.datast)

    def gen_base_vmx(self, fname):
        """ Opens a file with the name as fname, and puts the base 
            statements of a .vmx file into this
        """
        fhdl = open(fname, 'w')
        fhdl.write('.encoding = "UTF-8"\n')
        fhdl.write('config.version = "8"\n')
        fhdl.write('virtualHW.version = "7"\n')
        fhdl.write('pciBridge0.present = "TRUE"\n')
        fhdl.write('svga.present = "TRUE"\n')
        fhdl.write('pciBridge4.present = "TRUE"\n')
        fhdl.write('pciBridge4.virtualDev = "pcieRootPort"\n')
        fhdl.write('pciBridge4.functions = "8"\n')
        fhdl.write('pciBridge5.present = "TRUE"\n')
        fhdl.write('pciBridge5.virtualDev = "pcieRootPort"\n')
        fhdl.write('pciBridge5.functions = "8"\n')
        fhdl.write('pciBridge6.present = "TRUE"\n')
        fhdl.write('pciBridge6.virtualDev = "pcieRootPort"\n')
        fhdl.write('pciBridge6.functions = "8"\n')
        fhdl.write('pciBridge7.present = "TRUE"\n')
        fhdl.write('pciBridge7.virtualDev = "pcieRootPort"\n')
        fhdl.write('pciBridge7.functions = "8"\n')
        fhdl.write('virtualHW.productCompatibility = "hosted"\n')
        fhdl.write('memSize = "1108"\n')
        fhdl.write('sched.cpu.units = "mhz"\n')
        fhdl.write('powerType.powerOff = "soft"\n')
        fhdl.write('powerType.suspend = "hard"\n')
        fhdl.write('powerType.reset = "soft"\n')
        fhdl.write('guestOS = "other-64"\n')
        fhdl.write('toolScripts.afterPowerOn = "TRUE"\n')
        fhdl.write('toolScripts.afterResume = "TRUE"\n')
        fhdl.write('toolScripts.beforeSuspend = "TRUE"\n')
        fhdl.write('toolScripts.beforePowerOff = "TRUE"\n')
        fhdl.write('chipset.onlineStandby = "FALSE"\n')
        fhdl.write('sched.cpu.min = "0"\n')
        fhdl.write('sched.cpu.shares = "normal"\n')
        fhdl.write('sched.mem.min = "0"\n')
        fhdl.write('sched.mem.minSize = "0"\n')
        fhdl.write('sched.mem.shares = "normal"\n')
        fhdl.write('floppy0.present = "FALSE"\n')
        fhdl.write('replay.supported = "FALSE"\n')
        fhdl.write('replay.filename = ""\n')
        fhdl.write('ide0:0.redo = ""\n')
        fhdl.write('pciBridge0.pciSlotNumber = "17"\n')
        fhdl.write('pciBridge4.pciSlotNumber = "21"\n')
        fhdl.write('pciBridge5.pciSlotNumber = "22"\n')
        fhdl.write('pciBridge6.pciSlotNumber = "23"\n')
        fhdl.write('pciBridge7.pciSlotNumber = "24"\n')
        fhdl.write('vmci0.pciSlotNumber = "33"\n')
        fhdl.write('vmci0.id = "158687753"\n')
        fhdl.write('evcCompatibilityMode = "FALSE"\n')
        fhdl.write('vmotion.checkpointFBSize = "4194304"\n')
        fhdl.write('cleanShutdown = "FALSE"\n')
        fhdl.write('softPowerOff = "FALSE"\n')
        return (fhdl)

    def destroy_networks(self, bridge):
        # For ESXI the bridge class does all the cleanup, nothing to do here
        pass

    def start_networks(self, connections, br_type, br_name):
        # For ESXI the bridge class does all the setup. Nothing to do here
        pass

    def destroy_restart_stop_vms(self, vms, action):
        for vm in vms:
# find the vmid of this vm
            vm_name = vm.keys()[0]
            vm_datast = os.path.join(self.datast, vm_name)
            print ("Destroy vm %s %s" %(vm_datast, vm_name)
            proc = subprocess.Popen(['vim-cmd', 'vmsvc/getallvms', \
            '|' 'grep' , vm_name, '|' , 'cut' , '-f', '1' , \
            '-d' , '" "'], stdout=subprocess.PIPE)
            vm_id = proc.communicate()[0]
            subprocess.call(['vim-cmd', 'vmsvc/power.off', vm_id])
            if (action == 'restart'):
                subprocess.call(['vim-cmd', 'vmsvc/power.on', vm_id])
            elif (action == 'clean'):
                #subprocess.call(['rm' , vm_datast + '/' + vm_name +'*'])
                #subprocess.call('rmdir', vm_datast )
                pass
            elif (action == 'stop'):
                pass
            else:
                print ("Illegal argument to destroy_restart_stop")
        print ("In ESXI destroy VM")

    def create_vm(self, vm, tmp_dir, iso_dir):
        # Create the vm directory under the datastore
        vm_dir = os.path.join(self.datast, vm.name)
        subprocess.call(['mkdir', vm_dir])

        #Create the base .vmx file
        vmx_fil = os.path.join(vm_dir, vm.name + '.vmx')
        fhdl = self.gen_base_vmx(vmx_fil)
        fhdl.write('nvram = "%s.nvram"\n' %(vm.name))
        fhdl.write('displayName = "%s"\n' %(vm.name))
        
        #if there is a .iso file, then enable the cdrom option
        fname = os.path.join(iso_dir, vm.version+'.iso')
        if (os.path.isfile(fname)):
            fhdl.write('ide0:1.deviceType = "cdrom-image"\n')
            fhdl.write('ide0:1.fileName = "%s"\n' %(fname))
            fhdl.write('ide0:1.present = "TRUE"\n')

        #If there is a .vmdk file, then use that or create a new one
        fname = os.path.join(iso_dir, vm.version + '.vmdk')
        vmdk_fl = os.path.join(vm_dir, vm.name + '.vmdk' )
        if (os.path.isfile(fname)):
            subprocess.call(['cp', fname, vmdk_fl])
        else:
            subprocess.call(['vmkfstools', '-c', '16g', '-d' 'thin', '-a', \
            'ide', vmdk_fl])
        fhdl.write('ide0:0.fileName = "%s"\n' %(vmdk_fl))
        fhdl.write('ide0:0.mode = "independent-persistent"\n')
        fhdl.write('ide0:0.present = "TRUE"\n')

        # Fill up the network list
        intf_no = 0
        for i in vm.connections:
            fhdl.write('ethernet%d.virtualDev = "e1000"\n' %(intf_no))
            fhdl.write('ethernet%d.networkName = "%s"\n' %(intf_no, i))
            fhdl.write('ethernet%d.addressType = "generated"\n' %(intf_no))
            fhdl.write('ethernet%d.present = "TRUE"\n' %(intf_no))
            intf_no += 1
        # Now create the VM
        fhdl.close()
        proc = subprocess.Popen(['vim-cmd', 'solo/registervm', vmx_fil], 
                         stdout = subprocess.PIPE)
        vm_id = proc.communicate()[0]
        subprocess.call(['vim-cmd', 'vmsvc/power.on', vm_id])
        name_to_port = {}
        name_to_port[vm.name] = "vnc"
        return name_to_port

"""
Class that starts networks and VMs and also destroys them in KVM
"""
class KVM(Hypervisor):
    telnet_start_port = 20000  #Default port to start using for console
    def __init__(self, hyp_params):
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
        
        cmd_list = [
        'virt-install', 
         '--name=%s' % vm.name, 
         '--ram=1024', 
         '--watchdog','i6300esb,action=none']

        # If .iso is present add the cdrom option
        iso_fil = os.path.join(iso_dir, vm.version + '.iso')
        if (os.path.exists(iso_fil)):
            cmd_list.append('--cdrom=' + iso_fil)
        
        #If vmdk file is present add it as the disk
        vmdk_fil = os.path.join(iso_dir, vm.version + '.vmdk')
        tgt_fil = os.path.join(work_dir, vm.version + '.vmdk')
        if (os.path.exists(vmdk_fil)):
            form = 'vmdk'
            subprocess.cmd(['cp', vmdk_fil, tgt_fil])
            if (not(os.path.exists(iso_fil))):
                cmd_list.append('--boot=hd')
        else:
            form = 'qcow2'
            subprocess.call(['qemu-img', 'create', '-fqcow2', tgt_fil, '16G'])

        cmd_list.append('--disk=%s,format=%s,device=disk,bus=ide' 
                        %(tgt_fil, form)) 

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

        
    def destroy_restart_stop_vms(self, vms, action):
        for vm in vms:
            subprocess.call(['virsh','destroy', vm.keys()[0]])
            if action == 'clean':
                subprocess.call(['virsh','undefine',vm.keys()[0]])
            elif action == 'restart':
                subprocess.call(['virsh', 'start', vm.keys()[0]])
            elif action == 'stop':
                pass
            else:
                print ("Illegal argument to destroy_restart_stop_vms. Should be\
                        'clean', 'restart' or 'stop'")
