# SALI test project

This repository contains the 1.7.0 client and server code.

## Development requirements

Operating systems Mac OSX and Linux are supported. For some dependicies we recommend to use homebrew on Mac OSX.

Requirements:
 * QEMU (client testing)
 * Python 2.7 (server tools)

Recommendations:
 * Virtualenv and virtualenvwrapper

## Client

### Running tests
 * First start the webserver `./test_vm.sh webserver`
 * Edit files/cmdline and change your hostname in `SALI_MASTERSCRIPT`
 * Run `./test_vm.sh run` to start a virtual machine. (separate terminal)

#### Mapped ports
 * SSH 8022
 * SYSLOG 8514

## File stucture

 * docs : Contains some documentation and ideas for the future
 * client : Contains the shell script code for the embbedded Linux environment
 * CHANGELOG : What has changed since version 1.0.0
 * README.md : This file
 * `test_client.sh` : Allows you to test the client code in the SALI embedded environment

## Server

### Features
 * Create an image with rsync (uses ssh to start rsync on the golden-client)
 * Create a tar.gz image for bittorrent distribution
 * Generate a rsync daemon config
 * Bittorrent tracker
