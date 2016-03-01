# SALI Buildroot

## How to build

Download buildroot from buildroot.org and extract the tarball. Then issue the following commands
```
cd /tmp
wget https://buildroot.org/downloads/buildroot-2016.02-rc1.tar.gz
tar xvf buildroot-2016.02-rc1.tar.gz
git clone https://gitlab.com/surfsara/sali.git
cd buildroot-2016.02-rc1
make BR2_EXTERNAL=/tmp/sali/client sali_defconfig
make
```
