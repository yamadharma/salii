#  
#  Copyright (C) 2003 dann frazier <dannf@dannf.org>
#
#  $Id: InitrdFS.pm 2699 2004-02-17 06:35:19Z dannf $
# 
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

package BootGen::InitrdFS;

use strict;
use Carp;

use BootGen::InitrdFS::Cramfs;
use BootGen::InitrdFS::Ext2;

use vars qw(@fstypes);

use Util::Log qw(:all);
use Util::Cmd; # for which()

sub footprint {
    my $config = shift;

    foreach my $fstype (@fstypes) {
	if ($fstype->footprint($config)) {
	    return $fstype;
	}
    }
    return "";
}

1;
