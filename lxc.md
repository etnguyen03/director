# Director LXC VM architecture

 - Director talks to a libvirt backend, be it LXC or QEMU (I'm focusing on LXC first)
    - Uses ssh as a tunnel protocol, so Director needs passwordless SSH access to any servers where it runs VMs
    - Host object in database contains URL
 - VMs are created on libvirt with the name {user}-{uuid}
 - Hostname is the same as name
 - IP: Probably give it an internal IPv4, routed through LXC host.  Probably ephemeral as well?
 - Static IPv6 is fine



TODO: 
 - [ ] list
 - [ ] console
 - [ ] create
 - [ ] delete
 - [ ] info