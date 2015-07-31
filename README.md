#Network_Topology

#License   
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

#What does this tool do?
   This tool creates virtual machines and a network topology between them based on a 
   config file in JSON format present in the 'conf' directory.
   
   VMs can either be switch VMs or standard Linux VMs. It currently uses KVM 
   as the hypervisor and can be easily extended for using other hypervisors.
   It supports both Linux bridge and OpenVSwitch bridge as the network 
   bridges for interconnecting the VMs.
   
   nw_topo.py is the main script. It can be run with three options. Run it as 
   
      nw_topo.py --help
      
   to get a list of options.
   
   ISO_DIR is the place where you must put your ISO files and VMDK files if necessary 
   for the VM to boot. The tool loads these ISO files and creates either a blank disk 
   image or a copy of the VMDK file you have specified, in the working directory, 
   which is './working_dir'.
   
   The ISO files must be named as the version of the VM. For example a VM with version 
   of 'ubuntu_15' will have an ISO called 'ubuntu_15.iso' in the ISO_DIR. The same goes 
   for VMDK files.
   
#Installation
   Run
   
      git clone https://github.com/Pathangi-Jatinshravan/Network_Topology.git 
   
   to get the latest version of the tool.
   
   Also make sure the required packages are installed before running the nw_topo.py script. 
   You want:
   
   1)bridge-utils
   
   2)ovs-vsctl
   
   3)qemu-kvm
   
   4)libvirt-bin
   
   5)virt-manager  
   
   Move the ISO files of the VMs you want to be created, along with any VMDK files they need for booting, into a 
   directory, and specify this directory as the ISO_DIR in the config.json file under the 'COMMON' heading.
   
