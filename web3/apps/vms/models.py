import threading
import uuid

import libvirt
from django.core.cache import cache
from django.db import models
from django.utils.text import slugify

from .helpers import call_api
from ..sites.models import Site
from ..users.models import User


class VirtualMachineHost(models.Model):
    """Represents a host for virtual machines.

    Attributes:
        hostname
            The host to connect to (ex: lxc1.csl.tjhsst.edu).
    """
    hostname = models.CharField(max_length=255)

    @property
    def connection(self) -> libvirt.virConnect:
        if not hasattr(self, 'libvirt_connection'):
            conn = libvirt.open('lxc+ssh://root@{}/'.format(self.hostname))
            self.libvirt_connection = conn
        # TODO: figure out how to check if a connection is still open
        return self.libvirt_connection

    def __str__(self):
        return self.hostname


class VirtualMachine(models.Model):
    """Represents a virtual machine.

    Attributes:
        name
            The name of this virtual machine. The slugified version of this field is the host name of the machine.
        uuid
            The UUID of this virtual machine. Used by the API to identify virtual machines.
        description
            A description for the purpose of this virtual machine.
        owner
            The owner of this virtual machine. The owner can delete the machine and add other members.
        users
            The other users that have access to the virtual machine.
        site
            If this field is set, the site proxies all requests to the virtual machine.
    """
    name = models.CharField(max_length=255, unique=True)
    host = models.ForeignKey(VirtualMachineHost, on_delete=models.PROTECT)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, null=True)
    users = models.ManyToManyField(User, related_name='vms')
    site = models.OneToOneField(Site, related_name="virtual_machine", blank=True, null=True)

    def is_online(self):
        return self.host.connection.lookupByUUIDString(str(self.uuid)).isActive()

    @property
    def ips(self):
        # TODO fix this
        return ['1.2.3.4']

    @property
    def ip_address(self):
        ips = self.ips
        return ips[-1] if len(ips) else None

    @property
    def hostname(self):
        return slugify(self.name).replace("_", "-")

    def __str__(self):
        return self.name
