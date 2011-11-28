# SARA 2011 (c)
#
# Michel Scheerman: sali xcat plugin beta 0.1
#
# NOTE: This plugin is still in development, it is not yet compliant with the xcat standards. 
# Therefore problems could occur with certain node states or other unforseen results could occur.
#
# This plugin has been tested and is being used in a ppc64 environment.
#
# Usage: To use this plugin certain xcat database fields have to be filled accordingly. 
# Xcat table noderes: fields "netboot" and "installnic" have to be filled with the value "sali" and "eth[0..*]"
# Xcat table bootparams: fields: "kernel" and "addkcmdline" need to be filled with sali parameters.
# Xcat table nodetype: field "arch" value "ppc64"
#
# Example noderes: table entry: "p6108-mgmt",,"sali","192.168.86.1","192.168.86.1",,,"eth0","eth0",,,,,,,,
# Example bootparams: table entry: "p6108-mgmt","sali/ppc64/beta/vmlinuz",,"MONITOR_SERVER=si_monitor MONITOR_CONSOLE=yes PROTOCOL=bittorrent SCRIPTNAME=ppc64_sles11sp1_263245 BLACKLIST=lpfc STAGING=/tmp VERBOSELEVEL=2 SSHD=y rw",,,,,
# Example nodetype: "p6108-mgmt",,"ppc64",,,,,,
#

package xCAT_plugin::sali;
use Sys::Hostname;
use xCAT::Table;
use xCAT::Utils;
use xCAT::MsgUtils;
my $tftpdir = xCAT::Utils->getTftpDir();
1;

sub handled_commands
{
	return {
		nodeset => "noderes:netboot"
	}
}

sub preprocess_request
{
	my $req = shift;
	my $callback  = shift;
	my %sn;
	#if already preprocessed, go straight to request
	if (($req->{_xcatpreprocessed}) and ($req->{_xcatpreprocessed}->[0] == 1) ) { return [$req]; }
	my $nodes    = $req->{node};
	my $service  = "xcat";

	# find service nodes for requested nodes
	# build an individual request for each service node
	if ($nodes) {
 		$sn = xCAT::Utils->get_ServiceNode($nodes, $service, "MN");

  		# build each request for each service node

  		foreach my $snkey (keys %$sn)
  		{
			my $n=$sn->{$snkey};
			print "snkey=$snkey, nodes=@$n\n";
			my $reqcopy = {%$req};
			$reqcopy->{node} = $sn->{$snkey};
			$reqcopy->{'_xcatdest'} = $snkey;
			$reqcopy->{_xcatpreprocessed}->[0] = 1;
			push @requests, $reqcopy;
		}
		return \@requests;
	}
	else 
	{ # input error
		my %rsp;
		$rsp->{data}->[0] = "Input noderange missing. Useage: sali <noderange> \n";
		xCAT::MsgUtils->message("I", $rsp, $callback, 0);
		return 1;
	}
}

# Example usage: get_nodetype_table($request, $node)->{arch}
sub get_nodetype_table
{
	my $request	= shift;
	my $node	= shift;
	my $nodetype_table	= xCAT::Table->new('nodetype');
	my $nodetype_data = $nodetype_table->getNodesAttribs($request->{node}, ['os', 'arch', 'profile', 'provmethod']);
	my $node_nodetype_data = $nodetype_data->{$node}->[0];
	return $node_nodetype_data;
}

# Example usage: get_bootparams_table($request, $node)->{kernel}
sub get_bootparams_table
{
	my $request	= shift;
	my $node	= shift;
	my $bootparams_table	= xCAT::Table->new('bootparams');
	my $bootparams_data = $bootparams_table->getNodesAttribs($request->{node}, ['kernel', 'initrd', 'kcmdline', 'addkcmdline']);
	my $node_bootparams_data = $bootparams_data->{$node}->[0];
	return $node_bootparams_data;
}

# Example usage: get_noderes_table($request, $node)->{installnic}
sub get_noderes_table
{
	my $request	= shift;
	my $node	= shift;
	my $noderes_table	= xCAT::Table->new('noderes');
	my $noderes_data = $noderes_table->getNodesAttribs($request->{node}, ['installnic']);
	my $node_noderes_data = $noderes_data->{$node}->[0];
	return $node_noderes_data;
}

sub process_request
{
	my $request	= shift;
	my $callback	= shift;
	my $nodes	= $request->{node};
	my $command	= $request->{command}->[0];
	my $args	= $request->{arg};
	my $envs	= $request->{env};
	my $host	= hostname();
	my @args	= @$args;
	my @nodes	= @$nodes;
	my %rsp;
	my $open_pxe_config;
	my $i = 1;

	if ( "$args->[0]" eq "install" )
	{

		$rsp->{data}->[0] = "Setting the sali config in $tftpdir/etc/ for: ";
		xCAT::MsgUtils->message("I", $rsp, $callback, 0);

		foreach $node (@nodes)
		{
			$rsp->{data}->[$i] = "$node\n";
			open($open_pxe_config,'>',$tftpdir."/etc/".$node);
			print $open_pxe_config "timeout=5\n";
			print $open_pxe_config "image=".get_bootparams_table($request, $node)->{kernel}."\n";
			print $open_pxe_config "	label=sali\n";
			print $open_pxe_config "	initrd-size=32768\n";
			print $open_pxe_config "	append=\"DEVICE=".get_noderes_table($request, $node)->{installnic}." ".get_bootparams_table($request, $node)->{kcmdline}."\"\n";
			close($open_pxe_config);
			$i++;
		}
		xCAT::MsgUtils->message("I", $rsp, $callback, 0);

		return;
	}
	else
	{
		$rsp->{data}->[0] = "sali plugin: invalid argument\nAvailable argument is: install";
                xCAT::MsgUtils->message("I", $rsp, $callback, 0);
	}
}
