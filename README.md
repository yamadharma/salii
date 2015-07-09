# SALI test project

This repository contains the 1.7.0 client and server code. Please note that this repository is a work in progress.

## Development requirements

Operating systems Mac OSX and Linux are supported. For some dependicies we recommend to use homebrew on Mac OSX.

Requirements:
 * QEMU (client testing)
 * Python 2.7 (server tools)

Recommendations:
 * Virtualenv and virtualenvwrapper

## File stucture

 * docs : Contains some documentation and ideas for the future
 * client : Contains the shell script code for the embbedded Linux environment
 * server : Contains the SALI server tools
 * CHANGELOG : What has changed since version 1.0.0
 * README.md : This file
 * `test_client.sh` : Allows you to test the client code in the SALI embedded environment

## Client

### Running tests
 * First start the server `./test_vm.sh server`
 * Edit client/files/cmdline and change your hostname in `SALI_MASTERSCRIPT`
 * Run `./test_vm.sh run` to start a virtual machine. (separate terminal)

#### Mapped ports
 * SSH 8022
 * SYSLOG 8514

#### Client file structure
These are the SALI specific files
```
/etc/sali
    - console_file              # The motd when we just open the console
    - default_variables         # new file which contains the default values for variables
    - error_file                # motd when installation fails
    - error_startup_file        # motd when startup failes
/etc/sali_version               # Just like Debian but then for SALI
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
/lib/sali/functions             # Files are show in the orde they are sourced in the functions file
    - general.sh                # Contains functions that are used in all other files
    - network.sh                # Network related functions
    - ssh.sh                    # Configure and start ssh functions
    - initialize.sh             # Intialize function for the embedded SALI environment
    - scripts.sh                # Fetch and run script functions
    - torrent.sh                # Fetch image via torrent functions
    - rsync.sh                  # Fetch image via rsync functions
    - imaging.sh                # Fetch image functions (uses the rsync and torrent functions)
    - disks.sh                  # Partition, lvm, mdadm functions
    - deprecated.sh             # This file contains all deprectaed functions that will be removed in a future release of SALI
```

Also during runtime some SALI specific files are created:
```
/var/log/messages               # The syslog, also contains the output from the stdout
/var/cache/sali
    - installer_first_try       # To keep track if we already tried to fetch the master_script
    - master_script             # The actual master_script that has been downloaded
    - scripts/                  # A directory which contains the post and pre install scripts
    - variables                 # All variables of SALI are written here
    - disks/                    # Will contain information about the disks
        - sda                   # Will be created during the partition phase to keep track
                                # of which partitions are created
```

## Server

### Features
 * Create an image with rsync (uses ssh to start rsync on the golden-client)
 * Create a tar.gz image for bittorrent distribution
 * Generate a rsync daemon config
 * Bittorrent tracker
