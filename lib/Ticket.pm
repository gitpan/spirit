#!/usr/local/bin/perl -w
package Ticket;
use strict;
use vars qw ( $TICKET_UNKNOWN $WRONG_IP $version @ISA );
$TICKET_UNKNOWN = "-1";
$WRONG_IP = "-2";
use LkTyH;
@ISA = qw( LkTyH);           # Klasse LkTyH erben
$version = "0.2.0";
sub new {
my $type = shift;	# hole Objekttyp
my ($filename) = @_;	# hole Parameter
my $self = $type->SUPER::new( $filename);	
$self->{filename}    = $filename;
$self->{ticket_hash} = $self->{LkTyH_hash};
return bless $self, $type;
}
sub Create {
my $self = shift;			# hole Objektreferenz
my ($ip_adress, $username) = @_;	# hole Parameter
my $ticket = 0;
do {
$ticket = time();
srand ($ticket ^ ($$+($$<<15)));
$ticket .= int (rand (999999));
($ticket) = $ticket =~ /(..............)$/;
$ticket =~ s/(..)(..)(..)(..)(..)(..)(..)/$7$6$5$4$1$3$2/;
} while defined $self->{ticket_hash}{$ticket};
my ($timestamp) = Timestamp();
$self->{ticket_hash}->{$ticket} =
"$ip_adress\t$username\t$timestamp\t$timestamp";
return $ticket;
}
sub Check {
my $self = shift @_;
my ($ticket, $ip_adress) = @_;
my $value = $self->{ticket_hash}->{$ticket};
return $TICKET_UNKNOWN if ! defined $value;
my @field = split ("\t", $value);
return $WRONG_IP if $ip_adress ne $field[0];
$field[3] = Timestamp();
$self->{ticket_hash}->{$ticket} = join ("\t", @field);
return $field[1];
}
sub Get_Ticket_Timestamp {
my $self = shift @_;
my ($ticket) = @_;
my $value = $self->{ticket_hash}->{$ticket};
return $TICKET_UNKNOWN if ! defined $value;
my @field = split ("\t", $value);
return $field[3];
}
sub Get_All_Tickets {
my $self = shift @_;
my @key_list = keys ( %{$self->{ticket_hash}} );
return \@key_list;
}
sub Timestamp {
return time;
}
sub Dump_All {
my $self = shift;		# hole Objektreferenz
my ($ticket, $content);
while ( ($ticket, $content) = each (%{$self->{ticket_hash}}) ) {
print "$ticket:$content\n";
}
}
sub Delete {
my $self = shift @_;
my ($ticket) = @_;
my $value = $self->{ticket_hash}->{$ticket};
return -1 if ! defined $value;
delete $self->{ticket_hash}{$ticket};    
return 1;
}
1;
