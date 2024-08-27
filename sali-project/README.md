# SALI project
This repository contains the 2.0.0 client and server code. Please note that this repository is a work in progress.

We have a matrix room where you can ask questions:
 * https://matrix.to/#/#SALI:surf.nl
 * #SALI:surf.nl (if you have a client)

## Development requirements
Only Linux is supported as OS for running the SALI tools

Requirements:
 * QEMU (client testing)
 * wget
 * Python 3 (server tools)

Recommendations:
 * Virtualenv and virtualenvwrapper

## File structure
 * archive      : Contains the old-new Python code. Only used for reference
 * buildroot    : Contains the shell script code for the embbedded Linux environment
 * examples     : Contains examples configuration files for the SALI tools and buildroot env
 * sali         : Contains the SALI tools
 * CHANGELOG    : What has changed since version 1.0.0
 * README.md    : This file
 * sali-cli     : The main Python script for SALI tools
 * sali-test-client: A simple shell script for testing the buildroot env in qemu

## Client

### Building the buildroot for SALI
 1. Download buildroot and unpack it separate from this repository. In this example we will take `/tmp`
 2. `cd /tmp && wget https://buildroot.org/downloads/buildroot-2021.02.1.tar.gz`
 3. Unpack buildroot: `tar xvf buildroot-2022.11.1.tar.gz` and change directory to `cd buildroot-2022.11.1`
 4. Configure buildroot with the `sali_x86_64_defconfig` via the `BR2_EXTERNAL` method
    * `make BR2_EXTERNAL=/<path_2_your_source>/sali/buildroot sali_x86_64_defconfig`
 5. Now run `make xxhash`
 5. Now run `make zstd`
 5. Now run `make`

After building the images are available in the `output/images` directory in the buildroot dir.

### Updating buildroot/linux/busybox config
We assume you have already downloaded, extracted and configured the buildroot from the building instructions. Buildroot will update the corresponding files in the sali repository, so don't forget to commit them.

#### Updating buildroot configuration
 1. `make menuconfig`
 2. After modifying options, run `make savedefconfig`

Sometimes you get an error:
```
Makefile.legacy:9: *** "You have legacy configuration in your .config! Please check your configuration.".  Stop. 
```
Run `make menuconfig` ---> `Legacy config options` and disable the legacy option
   
#### Updating Linux configuration
 1. `make linux-menuconfig`
 2. After modifying options, run `make linux-update-defconfig`

 #### Updating Busybox configuration
 1. `make busybox-menuconfig`
 2. After modifying options, run `make busybox-update-config`

#### Running tests
 * Please note script only works on Linux
 * First start the server `./sali-test-client server`
 * Prepare the network (assumes you have a bridge device with name bridge0), `./sali-test-client network-prepare`
 * Run `./sali-test-client make-copy-run` to make buildroot, copy linux/initrd, start a virtual machine. (separate terminal)

#### Client file structure

These files are located in the rootfs_overlay in `buildroot/board/sali/common/rootfs_overlay`

```
/etc/sali
    - console_file              # the motd when we just open the console
    - default_variables         # new file which contains the default values for variables
    - error_file                # motd when installation fails
    - error_startup_file        # motd when startup failes
/etc/sali_version               # just like Debian but then for SALI
/etc/init.d
    - functions                 # the main file to source for using the wrapper commands
/etc/startup.d
    - S1_network                # configure and start network
    - S2_preparation            # fetch master_script and start the monitoring
    - S3_sshd                   # start sshd (if needed)
/etc/installer.d
    - S1_prepare                # scrub the disk (when asked for) and fetch the post/pre installation scripts
    - S2_pre_installation       # run the pre-installation scripts
    - S3_partition              # partition the disks
    - S4_imaging                # fetch/extract image
    - S5_post_installation      # run the post-installation scripts
    - S6_finalize               # umount disks
/lib/sali/functions             # files are shown in the order they are sourced in the functions file
    - general.sh                # contains functions that are used in all other files
    - network.sh                # network related functions
    - ssh.sh                    # configure and start ssh functions
    - initialize.sh             # initialize function for the embedded SALI environment
    - scripts.sh                # fetch and run script functions
    - torrent.sh                # fetch image via torrent functions
    - rsync.sh                  # fetch image via rsync functions
    - imaging.sh                # fetch image functions (uses the rsync and torrent functions)
    - disks.sh                  # partition, lvm, mdadm functions
    - deprecated.sh             # this file contains all deprecated functions that will be removed in a future release of SALI
```

Also during runtime some SALI specific files are created:
```
/var/log/messages               # the syslog, also contains the output from the stdout
/tmp/sali
    - installer_first_try       # to keep track if we already tried to fetch the master_script
    - master_script             # the actual master_script that has been downloaded
    - scripts/                  # a directory which contains the post and pre install scripts
    - variables                 # all variables of SALI are written here
```

## Server

### Build server tools

To fetch an image from a client we need the tool `sali-cli`. This is an python tool that can be converted to a standalone
executable:
 * `pipenv --python 3`
 * `pipenv shell`
 * `pipenv install --dev`
 * `pipenv run pyinstaller --onefile sali-cli`
 * install the `sali-cli` utility in your path
 * `cp -a examples/sali-cli-config` /etc/sali and adjust to your environment for new installations

Now create an golden image from a client via `sali-cli`:
 1. `sali-cli getimage <server> <image-name>`
 2. `sali-cli rsyncconfig`

### Requirements
 * Python 3.7+
 * Transmission 2.94+
 * Opentracker (see wiki for buildinstriuctions)

### Features
 * Create an image with rsync (uses ssh to start rsync on the golden-client)
 * Create a tar.gz image for bittorrent distribution
 * Generate a rsync daemon config
