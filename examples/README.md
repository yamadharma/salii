# EXAMPLES explanation

There are 2 directories here:
> sali-cli-config
>   This are the configuration files for the `sali-cli` utility and must be copied to `/etc/sali`
>
> SALI installation_scripts
>   - client installation example scripts
>   - pre/post-installations example scripts
>

## post-install/systemd_configure_network

This scripts will configure the systend network devices. It can handle:
 * static interfaces
 * dhcp interfaces
 * bonding

The file needs an interface definition file so it can look up the `mac-address` of the
interface and know how to configure it, eg:
```
# mac iface_label <dhcp|static> iftype ip netmask gateway cf_cluster cf_hub key_role
#
# Example file
aa:bb:cc:dd:ee:00 vlan1 dhcp r1n1 192.168.0.2 255.255.255.0 192.168.0.1 r1n1.mgt.liza.surf.nl etp boot-server.mgt.liza.surf.nl compute
aa:bb:cc:dd:ee:01 vlan2 dhcp r1n1 192.168.1.2 255.255.255.0 192.168.1.1 r1n1.liza.surf.nl etp boot-server.liza.surf.nl disabled
aa:bb:cc:dd:ee:02 vlan3 static r1n1 192.168.2.2 255.255.255.0 192.168.2.1:default r1n1.prod.surf.nl etp boot-server.prod.surf.nl disabled
```
