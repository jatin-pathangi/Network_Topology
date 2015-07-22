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

import subprocess

class Bridge(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def add_bridge(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def del_bridge(self, *args, **kwargs):
        pass

class LinuxBridge(Bridge):
    def __init__(self, name):
        self.name = name

    def add_bridge(self):
        subprocess.call(['brctl', 'addbr', self.name])

    def del_bridge(self):
        subprocess.call(['brctl', 'delbr', self.name])

class OVSBridge(Bridge):
    def __init__(self, name):
        self.name = name

    def add_bridge(self):
        subprocess.call(['ovs-vsctl', 'add-br', self.name])

    def del_bridge(self):
        subprocess.call(['ovs-vsctl', 'del-br', self.name])
