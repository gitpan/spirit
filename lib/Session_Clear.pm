#!/usr/local/bin/perl -w
package Session_Clear;
use strict;
use Ticket;
sub Delete_Session {
my (@ticket) = @_;       # aktuelles Ticket
my $ticket_obj = new Ticket( $IDE::Ticket_File);    
my $ticket;
foreach $ticket ( @ticket) {
my $status = $ticket_obj->Delete($ticket);
unlink 
"${IDE::Session_Dir}/${ticket}.dir", 
"${IDE::Session_Dir}/${ticket}.pag",
"${IDE::Session_Dir}/${ticket}.lock";
}	
1;
}
sub Obsolete_Sessions {
my @session_list;                 # Liste aller Sitzungen, die veraltet sind
my $ticket_obj = new Ticket( $IDE::Ticket_File);    
my $ticket_list_ref = $ticket_obj->Get_All_Tickets();
my $ticket;
foreach $ticket ( @{$ticket_list_ref} ) {
my $ticket_time = $ticket_obj->Get_Ticket_Timestamp($ticket);
my $current_time = $ticket_obj->Timestamp();
my $diff_time = ($current_time - $ticket_time);
push @session_list, $ticket if $diff_time > 60*60*24 ;
}
return \@session_list;
}
1;
