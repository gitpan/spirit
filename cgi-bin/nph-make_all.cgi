#!/usr/bin/perl
BEGIN { 
$0 =~ m!^(.*)[/\\][^/\\]+$!;    # Windows NT Netscape Workaround
chdir $1;
require "../etc/ide.cnf";		# Konfigurationsdatei fuer die IDE
unshift ( @INC, $IDE::Lib);
}
use strict;
use CGI;
use Ticket;
use Cwd;
use File::Path;
use Depend;
use Config;
use Project;
main: {
$| = 1;
my $q = new CGI;
print $q->header (
-type	=>	'text/html',
-nph	=>	1
);
my $ticket = $q->param('ticket');
my $th = new Ticket ($IDE::Ticket_File);
my $username;
$username = $th->Check ($ticket, $ENV{REMOTE_ADDR});
if ( $username < 0 ) {
print "Zugriffs-Fehler\n";
exit;
}
$th = undef;
require "$IDE::Config_Dir/${username}.pl";
HTML_Header();
my $drivers = [ 'cipp' ];
Make_All ($q, $drivers);
HTML_Footer();
}
sub HTML_Header {
my $font = qq{<FONT FACE="$IDE::Font" SIZE=$IDE::Font_Size>};
print <<__HTML_CODE;
<HTML><HEAD><TITLE>spirit</TITLE></HEAD>
<BODY BGCOLOR=$USER::BG_Color TEXT="$USER::Text_Color"
ALINK="$USER::Link_Color" VLINK="$USER::Link_Color"
LINK="$USER::Link_Color">
$font
<H2>Neuübersetzung des Projektes</H2>
__HTML_CODE
}
sub HTML_Footer {
print "</BODY></HTML>\n";
}
sub Make_All {
my ($q, $drivers) = @_;
my $project = $q->param('project');
my $pf = new Struct_File ($IDE::Project_File);
my $project_dir = $pf->Read ($project, "DIRECTORY");
$pf = undef;
if ( $IDE::OS != 1 ) {
print "<P><B>Lösche den Produktionsbereich...</B>\n";
print "<BLOCKQUOTE>";
my $deldir = "$project_dir/prod/cgi-bin/$project";
print "$deldir...<BR>\n";
rmtree $deldir;
mkdir $deldir, 0770;
$deldir = "$project_dir/prod/htdocs/$project";
print "$deldir...<BR>\n";
rmtree $deldir;
mkdir $deldir, 0770;
$deldir = "$project_dir/prod/config";
print "$deldir...<BR>\n";
rmtree $deldir;
mkdir $deldir, 0770;
print "</BLOCKQUOTE>\n";
} else {
print "<P><B><FONT COLOR=red>Windows NT: Lösche den ".
"Produktionsbereich NICHT!</FONT></B>\n";
}
my $driver;
foreach $driver (@{$drivers}) {
my ($object, $object_type);
if ( $driver eq 'cipp' ) {
$object = "$project.Grundeinstellungen";
$object_type = "cipp-driver-config";
}
Make_One_Driver ($q, $driver, $object, $object_type);
}
}
sub Make_One_Driver {
my ($q, $driver, $object, $object_type) = @_;
my $ticket  = $q->param('ticket');
my $project = $q->param('project');
my $query_string =
"event=make_all&ticket=$ticket&object=$object&".
"object_type=$object_type&project=$project";
my $dupe;
if ( not $IDE::OS ) {
$dupe = "2>&1";
}
my $old_dir = cwd();
chdir "$IDE::Driver_Dir/$driver";
my %env = %ENV;		# Environment sichern
%ENV = ();		# und löschen (sonst liest CGI.pm die Parameter nicht ein)
$ENV{REMOTE_ADDR} = $env{REMOTE_ADDR};	# für Ticket Check
open ( DRVR, "$Config{perlpath} driver.cgi \"$query_string\" $dupe |");
%ENV = %env;
while (<DRVR>) {
print;
}
if ( ! close( DRVR) ) {
print "Systemfehler bei internem CGI-Aufruf: $!\n";
}
chdir $old_dir;
}
