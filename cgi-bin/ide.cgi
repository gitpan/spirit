#!/usr/bin/perl
BEGIN {	
$0 =~ m!^(.*)[/\\][^/\\]+$!;    # Windows NT Netscape Workaround
chdir $1;
require "../etc/ide.cnf";       # Konfigurationsdatei fuer die IDE
unshift ( @INC, $IDE::Lib);
}
use Lock;		     # Modul für Objektsperren
use CGI;                     # CGI-Methoden 
use File::Copy;              # Modul zum Kopieren von Dateien oder Dateihandles
use Passwd;                  # Methoden zur Bearbeitung der User-Passwd Datei
use Ticket;                  # Methoden zur Bearbeitung des User-Tickets
use Struct_File;             # Methoden zur Bearbeitung einer Hash-Datei
use Project;                 # Methoden zur Bearbeitung der Project-Datei
use Configure;               # Methoden zur Bearbeitung der Konfigurationsparameter
use Session_Clear;           # Funktionen, um veraltete Sitzungen zu loeschen
use strict;
my $TRUE = 1;
my $FALSE = 0;
my $version;
$version = "0.1.2";          # derzeitige Version
my $query = new CGI;            # CGI-Objekt anlegen
my ( $FONT, $FNTB, $FNTE);
sub set_fonts {
$FONT = "<font face=$USER::Font Size=$USER::Font_Size>";
$FNTB = "<td>${FONT}";
$FNTE = "</font></td>";
}
my $error_title = 
"Fehlermeldung";
my $ticket_error = 
"<B>Sie haben keinen Zugriff auf diese Seite.".
"Sie m&uuml;ssen sich erst im System anmelden<blink>!</blink></B>";
{
my $switch = $query->param('make') || '';
SWITCH: {    
&Login(), last if $switch eq 'login';
&Menu_Control(), last if $switch eq 'menu';
&Blank_Page(), last if $switch eq 'blank';
&User_Control(), last if $switch =~ m/^usr_/;
&Logout(), last if $switch eq 'logout';
&Project_Control(), last if $switch =~ m/^prj_/;
&Show_Logo(), last if $switch eq 'logo';
&Menu_Frame(), last if $switch eq 'menuframe';
&Change_Password(), last if $switch eq 'cnf_password';
&Config_Control(), last if $switch eq 'cnf_edit';
&Ask_For_Userdelete(), last if $switch eq 'ask_for_userdelete';
&Ask_For_Projectdelete(), last if $switch eq 'ask_for_projectdelete';
&Show_Login_Page();
}
}
sub Ask_For_Delete{
my ( $title, $message, $hidden_field_hash_ref) = @_;
my ( $key, $value);
my $hiddenfields = '';
while ( ( $key, $value) = each(%{$hidden_field_hash_ref})) {
$hiddenfields .= 
qq{<input type=hidden name='$key' value='$value'>\n};
}
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html>
<head><title>$IDE::Title</title></head>
<body bgcolor=$USER::BG_Color text=$USER::Text_Color
alink=$USER::Link_Color link=$USER::Link_Color 
vlink=$USER::Link_Color>
<font face=$USER::Font Size=$USER::Font_Size>
<h1>$title</h1>
<hr><p>
<b>$message</b>
<blockquote>
<form name="ask_for_delete" action="$IDE::Ide_Url" method=post>
<table bgcolor=$USER::Table_Color BORDER=1>
<tr><td>
<table><tr><td colspan=2><font FACE=$USER::Font size=$USER::Font_Size>
</font></td></tr>
<tr><td><font face=$USER::Font size=$USER::Font_Size>
<input type=button value=" L&ouml;schen " 
onclick="document.ask_for_delete.submit()">
<input type=button value=" Abbrechen "
onClick="document.ask_for_delete.make.value='blank';
document.ask_for_delete.submit()">
</font></td></tr>
</table></table>
$hiddenfields
</blockquote></form>
</font>    
</body>
</html>
__HTML_CODE
}
sub Ask_For_Projectdelete{
my $projects = join( "\t", $query->param('project'));
my $ticket = $query->param('ticket');    
my %hidden_field_hash = (project => $projects,
make => 'prj_delete',
ticket => $ticket,
ask => 'true');
$projects =~ s/\t/, /g;
my $message = ( $projects =~ m/,/) ?'Sollen die': 'Soll das';
$message .= " Projekt <em>$projects</em> wirklich gel&ouml;scht werden";
Ask_For_Delete( 'Projekte l&ouml;schen',
$message,
\%hidden_field_hash);
}
sub Ask_For_Userdelete{
my $user = join( "\t", $query->param('user'));
my $ticket = $query->param('ticket');    
my %hidden_field_hash = (user => $user,
make => 'usr_delete',
ticket => $ticket,
ask => 'true');
$user =~ s/\t/, /g;
my $message = ( $user =~ m/,/) ?'Sollen die': 'Soll der';
$message .= " Benutzer <em>$user</em> wirklich gel&ouml;scht werden";
Ask_For_Delete( 'Benutzer l&ouml;schen',
$message,
\%hidden_field_hash);
}
sub Blank_Page {
my $ticket_obj = new Ticket( $IDE::Ticket_File);    
my $ticket = $query->param('ticket');
my $ip_address = $query->remote_addr();
my $username = $ticket_obj->Check($ticket, $ip_address);
if ( $username lt "0") {
&Show_Message( $error_title, $ticket_error, 'logout');
return;
}
require "$IDE::Config_Dir/${username}.pl";  &set_fonts;
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html>
<head><title>$IDE::Title</title></head>
<body bgcolor=$USER::BG_Color text=$USER::Text_Color
alink=$USER::Link_Color link=$USER::Link_Color 
vlink=$USER::Link_Color>
<font face=$USER::Font Size=$USER::Font_Size>
</font>    
</body>
</html>
__HTML_CODE
}
sub Change_Password {
my $title = "Kennwort &auml;ndern";
my $ticket_obj = new Ticket( $IDE::Ticket_File);
my $passwd_obj = new Passwd( $IDE::Passwd_File);
my $ticket = $query->param('ticket');
my $ip_address = $query->remote_addr();
my $username = $ticket_obj->Check($ticket, $ip_address);
if ( $username lt "0") {
&Show_Message( $error_title, $ticket_error, 'logout');
return;
}
require "$IDE::Config_Dir/${username}.pl"; &set_fonts;
my $passwd = '';         # Kennwort
my $project_str;         # Projekte, an denen der Benutzer beteiligt ist
my $right_str;	     # Benutzerrechte
$passwd_obj->Get_User( $username, \$right_str, \$project_str);    
my $status = $TRUE;      # Fehlerstatus
my $message;             # Meldungstext
my $enter = $query->param('enter') || '';
if ( $enter eq 'TRUE') {
my $oldpasswd = $query->param('oldpasswd');
if ( $passwd_obj->Check_Passwd( $username, $oldpasswd) == $TRUE) {
&User_Get_Content( $passwd_obj, \$passwd, \$right_str, 
\$project_str, \$status);
if ( $status eq $TRUE) {
$message =  "Das Kennwort wurde ge&auml;ndert";
&Show_Message( $title, $message);
return;
}
else {	    
$message = ($status eq 'PASSWORD_INCORRECT') ? 
"Die Eintr&auml;ge f&uuml;r das Kennwort sind unterschiedlich" :
"Sie haben kein neues Kennwort angegeben";
}
}
else {
$message = "Das Kennwort ist falsch";
$status = $FALSE;
}
}
my $input_passwd_size = 15; 
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html><head><title>$IDE::Title</title></head>
<body bgcolor=$USER::BG_Color text=$USER::Text_Color
alink=$USER::Link_Color link=$USER::Link_Color 
vlink=$USER::Link_Color>
<font face=$USER::Font Size=$USER::Font_Size>
<h1>$title</h1>
<form name="chpasswd" action="$IDE::Ide_Url" method="get"><hr>
<input type="hidden" name="ticket" value="$ticket">
<input type="hidden" name="make" value="cnf_password">
<input type="hidden" name="enter" value="TRUE">
<input type="hidden" name="user" value="$username">
<blockquote>
<table bgcolor="$USER::Table_Color" border=1> <tr><td>
<table>
<tr>${FNTB}
Benutzername:</td>${FNTB} $username ${FNTE}</tr><tr>${FNTB}
altes Kennwort: ${FNTE}${FNTB}
<input type="password" name="oldpasswd" size="$input_passwd_size" >
${FNTE}</tr><tr><td colspan=2><hr></td></tr><tr>${FNTB}
neues Kennwort: ${FNTE}${FNTB}
<input type="password" name="passwd1" value="$passwd" size="$input_passwd_size" >
${FNTE}</tr><tr>${FNTB}
Wiederholung des neuen Kennworts:${FNTE}${FNTB}
<input type="password" name="passwd2" value="$passwd" size="$input_passwd_size" >
${FNTE}</tr></table></table>
</blockquote><hr><blockquote>
<input type="button" value="&Auml;ndern" onClick="document.chpasswd.submit()">
</blockquote>
</form></font>
<font face=$USER::Font size=$USER::Font_Size color=$USER::Error_Color>
__HTML_CODE
print $message . "<blink>!</blink>" unless $status eq $TRUE;
print "</font></body></html>\n";
}
sub Config_Control {
my $make = $query->param('make');
my $ticket_obj = new Ticket( $IDE::Ticket_File);
my $passwd_obj = new Passwd( $IDE::Passwd_File);
my $ticket = $query->param('ticket');
my $ip_address = $query->remote_addr();
my $username = $ticket_obj->Check($ticket, $ip_address);
if ( $username lt "0") {
&Show_Message( $error_title, $ticket_error, 'logout');
return;
}
require "$IDE::Config_Dir/${username}.pl";  &set_fonts;
my $config_obj = new Configure( $IDE::Config_File, $username);
my $cnf_hash_ref = $config_obj->Get_Items( $username);
my $cnfevent = $query->param('cnfevent') || '';
if ( $cnfevent eq 'save' or $cnfevent eq 'default') {
my ( $i, $content);
for $i ( 0 .. $#IDE::Para_Desc) {
if ( defined $IDE::Para_Desc[$i][0] ) {
if ( $query->param('cnfevent') eq 'default') {
eval "\$content = \$IDE::$IDE::Para_Desc[$i][0]";
}
else {
$content = $query->param( $IDE::Para_Desc[$i][0]);
}
$config_obj->Write( $username, $IDE::Para_Desc[$i][0], $content);
}
}
my $message =  "Die Einstellungen wurden &uuml;bernommen.";
&Show_Message( "Konfiguration bearbeiten", $message, 'onload');
}
else {
&Config_Form( $username, $ticket, $make, $cnf_hash_ref);
}
}
sub Config_Form {
my ($username,
$ticket,
$make,
$cnf_hash_ref) = @_;  # Uebergabeparameter
my $input_size = 30;      # Breite der Eingabefelder
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html>
<head><title>$IDE::Title</title></head>
<body bgcolor=$USER::BG_Color text=$USER::Text_Color
alink=$USER::Link_Color link=$USER::Link_Color 
vlink=$USER::Link_Color>
<font face=$USER::Font Size=$USER::Font_Size> 
<h1>Konfiguration bearbeiten</h1>
<form name="cnfcontrol" action="$IDE::Ide_Url" method="post"><hr>
<input type="hidden" name="make" value="$make">
<input type="hidden" name="ticket" value="$ticket">
<input type="hidden" name="cnfevent">
<blockquote>
<table bgcolor="$USER::Table_Color" border=1> <tr><td>
<table>
__HTML_CODE
my ( $i, $content);
for $i ( 0 .. $#IDE::Para_Desc) {
if ( defined $IDE::Para_Desc[$i][0] ) {
$content = $cnf_hash_ref->{$IDE::Para_Desc[$i][0]};
print "<tr>${FNTB}$IDE::Para_Desc[$i][1]:${FNTE}${FNTB}\n";
print "<input type=\"text\" name=\"$IDE::Para_Desc[$i][0]\" ".
"value=\"$content\" size=\"$input_size\">\n";
print "${FNTE}</tr>\n";
} else { 
print "<tr><td colspan=2>${FONT}<b>$IDE::Para_Desc[$i][1]</b>";
print "${FNTE}</tr>\n";
}
}
print <<__HTML_CODE;
</table></table>
</blockquote><p><hr>
<blockquote><input type="button" value="Speichern"
onClick="document.cnfcontrol.cnfevent.value='save';document.cnfcontrol.submit()">
<input type="button" value="Vorgabewerte"
onClick="document.cnfcontrol.cnfevent.value='default';document.cnfcontrol.submit()">
</blockquote>
</form>
</font>    
</body>
</html>
__HTML_CODE
}
sub Login {
my $passwd_obj = new Passwd( $IDE::Passwd_File);
my $username = $query->param('user') || '';
my $passwd = $query->param('passwd') || '';
my $status = $passwd_obj->Check_Passwd( $username, $passwd); 
if ( $status == $TRUE) {
my $session_list_ref = &Session_Clear::Obsolete_Sessions();
&Session_Clear::Delete_Session( @$session_list_ref);
my $ticket_obj = new Ticket( $IDE::Ticket_File);
my $ip_address = $query->remote_addr();
my $ticket = $ticket_obj->Create( $ip_address, $username);
if ( -e "${IDE::Config_Dir}/session_$username.dir" and 
-e "${IDE::Config_Dir}/session_$username.pag" ) {
copy ( "${IDE::Config_Dir}/session_$username.dir",
"${IDE::Session_Dir}/${ticket}.dir");
copy ( "${IDE::Config_Dir}/session_$username.pag",
"${IDE::Session_Dir}/${ticket}.pag");
}
&Main_Menu( $ticket);
} 
else {
&Show_Message("Autorisierung fehlgeschlagen",
" Sie haben sich nicht korrekt autorisiert oder Ihre".
" IP-Adresse ist nicht korrekt.",
"login", 
{user => "$username"});
}
}
sub Logout {
my $ticket_obj = new Ticket( $IDE::Ticket_File);    
my $ticket = $query->param('ticket');    
my $ip_address = $query->remote_addr();
my $username = $ticket_obj->Check($ticket, $ip_address);
my $status = $ticket_obj->Delete($ticket);
if ( -e "${IDE::Session_Dir}/${ticket}.dir" and 
-e "${IDE::Session_Dir}/${ticket}.pag" ) {
copy ( "${IDE::Session_Dir}/${ticket}.dir", 
"${IDE::Config_Dir}/session_$username.dir");
copy ( "${IDE::Session_Dir}/${ticket}.pag", 
"${IDE::Config_Dir}/session_$username.pag");
unlink 
"${IDE::Session_Dir}/${ticket}.dir", 
"${IDE::Session_Dir}/${ticket}.pag",
"${IDE::Session_Dir}/${ticket}.lock";
}
if ( $status != $TRUE ) {
&Show_Message( $error_title, $ticket_error, 'logout');
}
else {
&Show_Login_Page()
}
}
sub Main_Menu {
my $ticket = shift;      # Uebergabeparameter
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html>
<head><title>$IDE::Title</title></head>
<frameset cols="$IDE::Main_Frame_Size" border=1>
<frame src="${IDE::Ide_Url}?make=menu&ticket=$ticket" name="CONTROL">
<frame src="${IDE::Ide_Url}?make=blank&ticket=$ticket" name="ACTION">
</frameset>
</html>
__HTML_CODE
}
sub Show_Logo {
print <<__HTML_CODE;
Content-type: text/html
<html>
<body bgcolor=#ffffcc>
<img src="$IDE::Logo_Url">
</body>
</html>
__HTML_CODE
}
sub Menu_Control {
my $ticket_obj = new Ticket( $IDE::Ticket_File);    
my $passwd_obj = new Passwd( $IDE::Passwd_File);
my $ticket = $query->param('ticket');
my $ip_address = $query->remote_addr();
my $username = $ticket_obj->Check($ticket, $ip_address);
if ( $username lt "0") {
&Show_Message( $error_title, $ticket_error, 'logout');
return;
}
require "$IDE::Config_Dir/${username}.pl";  &set_fonts;
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html>
<head><title>$IDE::Title</title></head>
<body onLoad="parent.ACTION.location.href='$IDE::Ide_Url?make=blank&ticket=$ticket'"
bgcolor=$USER::BG_Color text=$USER::Text_Color
alink=$USER::Link_Color link=$USER::Link_Color 
vlink=$USER::Link_Color>${FONT}
<h1>Hauptmen&uuml;</h1>
Benutzer: <b>${username}</b><p><hr>
<b>Projekt</b><p>
<table bgcolor="$USER::Menue_BG_Color" width="100%" border=1>
__HTML_CODE
print "<tr>${FNTB}<a href=\"$IDE::Ide_Url?make=prj_new&ticket=".
"$ticket\"target=ACTION>neu</a>${FNTE}</tr>" 
if $passwd_obj->Check_Admin_Access( $username, "PROJECT") == $TRUE; 
print "<tr>${FNTB}<a href=\"$IDE::Ide_Url?make=prj_edit&ticket=$ticket\" ".
"target=ACTION>bearbeiten</a>${FNTE}</tr>";
print "<tr>${FNTB}<a href=\"$IDE::Ide_Url?make=prj_delete&ticket=$ticket\"". 
"target=ACTION>l&ouml;schen</a>${FNTE}</tr>"
if ( $passwd_obj->Check_Admin_Access( $username, "PROJECT") == $TRUE);
print "</table><p> <hr>\n";
if ( $passwd_obj->Check_Admin_Access( $username, "USER") == $TRUE) {
print <<__HTML_CODE;
<b>Benutzer</b><p>
<table bgcolor="$USER::Menue_BG_Color" width="100%" border=1>
<tr>${FNTB}
<a href="$IDE::Ide_Url?make=usr_new&ticket=$ticket" 
target=ACTION>neu</a>
${FNTE}</tr><tr>${FNTB}
<a href="$IDE::Ide_Url?make=usr_edit&ticket=$ticket" 
target=ACTION>bearbeiten</a>
${FNTE}</TR><TR>${FNTB}
<a href="$IDE::Ide_Url?make=usr_delete&ticket=$ticket" 
target=ACTION>l&ouml;schen</a>
${FNTE}</tr></table>
<p> <hr>
__HTML_CODE
}
print <<__HTML_CODE;
<b>Konfiguration</b><p>
<table bgcolor="$USER::Menue_BG_Color" width="100%" border=1>
<tr>${FNTB}
<a href="$IDE::Ide_Url?make=cnf_edit&ticket=$ticket" 
target=ACTION>bearbeiten</a>
${FNTE}</tr><tr>${FNTB}
<a href="$IDE::Ide_Url?make=cnf_password&ticket=$ticket"
target=ACTION>Kennwort</a>
${FNTE}</tr></table>
<p> <hr>
<table bgcolor="$USER::Menue_BG_Color" width="100%" border=1>
<tr><p>${FNTB}<b>
<a href="$IDE::Ide_Url?make=logout&ticket=$ticket" 
target="spirit">Abmelden</a>
</b>${FNTE}</tr></table>
</font>
</body>
</html>
__HTML_CODE
my $project = $query->param('project');
if ( defined $project ) {
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $project_dir = $ph->Get_Project_Dir($project);
my $Lock = new Lock ($project, "$project_dir/src", $IDE::Session_Dir);
$Lock->Delete ($ticket);
$Lock = undef;
}
}
sub New_Driver {
my ($project,
$username) = @_;
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $driver_name;
foreach $driver_name ( @IDE::Used_Drivers) {
my $object_types = $ph->{driver_file}->Read
($driver_name, "OBJECT_TYPES");
if ( $object_types =~ m/${driver_name}-driver-config/) {
my $error = $ph->Add_Object( $project, $project, "Grundeinstellungen", 
"$driver_name:${driver_name}-driver-config",
"$driver_name-Konfiguration", $username);
die $error if defined $error;
}
else {
my $used_drivers = $ph->{project_file}->Read ($project, "USED_DRIVERS");
$used_drivers .= "\t$driver_name";
$used_drivers =~ s/^\t//;
$ph->{project_file}->Write ($project, "USED_DRIVERS", $used_drivers);   
}
}
}
sub Project_Control {
my $make = $query->param('make');
my $tmp_make = $make; 
my %message = (
$Project::PROJECT_ALREADY_EXIST => 
'Es existiert schon ein Projekt mit diesem Namen. '.
'Bitte w&auml;hlen Sie einen anderen Namen.',
$Project::UNKNOWN_PROJECT =>
'Ein Projekt unter diesem Namen ist dem System nicht bekannt. '.
'Bitte w&auml;hlen Sie einen anderen Namen.',
$Project::DIRECTORY_NOT_CREATED =>
'Das Projektverzeichnis konnte nicht angelegt werden.<br>'.
'Bitte &uuml;berpr&uuml;fen Sie den angegebenen Pfadnamen und '.
'die Zugriffsrechte f&uuml;r das System.',
$Project::DIRECTORY_NOT_DELETED =>
'Das Projektverzeichnis konnte nicht gel&ouml;scht werden.'.
'Der Zustand des Projekts ist nicht einwandfrei.',
'PROJECT_CONTAINS_NO_DRIVER' =>
'Sie haben f&uuml;r Ihr Projekt keinen Treiber ausgew&auml;hlt.',
'WRONG_PATH_NAME' =>
'Der Verzeichnisname ist ung&uuml;ltig. Bitte geben Sie den '.
'vollst&auml;ndigen Verzeichnisnamen an.',
'DIRECTORY_ALREADY_EXISTS' =>
'Das Verzeichnis existiert schon. Bitte w&auml;hlen Sie ein Verzeichnis,'.
' das noch nicht existiert.',
);                       # Fehlermeldungen fuer den Benutzer
my $status;              # Fehler- und Statuswert
my $ticket_obj = new Ticket( $IDE::Ticket_File);
my $passwd_obj = new Passwd( $IDE::Passwd_File);
my $ticket = $query->param('ticket');
my $ip_address = $query->remote_addr();
my $username = $ticket_obj->Check($ticket, $ip_address);
if ( $username lt "0") {
&Show_Message( $error_title, $ticket_error, 'logout');
return;
}
require "$IDE::Config_Dir/${username}.pl"; &set_fonts;
my $make_str;            # Zeichenkette mit der Aktion ohne Praefix
($make_str = $make) =~ s/^prj_//;
my %make_hash = (
'new' => "anlegen",
'edit' => "bearbeiten",
'delete' => "l&ouml;schen",
);
my $title = "Projekt $make_hash{$make_str}";
my $project_obj = new Project( $IDE::Project_File, $IDE::Driver_File);
my $project;             # Projektname
$project = $query->param('project') || '';
SWITCH: {
if ( $make_str eq 'new') {
if ( $project ne '')  {
my ( $prjdir, $prjdesc, $driver_str, $copyright);
$passwd_obj = undef;
&Project_Get_Content( $project, \$prjdir, \$prjdesc,
\$driver_str, \$copyright,
\$status, $username, $project_obj);
if ( $status eq $TRUE ) {
$project_obj = undef;
$ticket_obj = undef;
New_Driver( $project);
my $open_folders = new LkTyH ($IDE::Session_Dir.$ticket);
$open_folders->{LkTyH_hash}->{$project} = 1;
my $message =
"Das Projekt <em>$project</em> wurde".
" erfolgreich angelegt.";
&Show_Message( $title, $message);
}
else {
&Project_Form( $make_hash{$make_str}, $project, $prjdir, 
$prjdesc, $driver_str, $copyright, 
$message{$status});
}
}
else {
&Project_Form( $make_hash{$make_str});
}
last SWITCH;
}
if ( $make_str eq 'edit') {
if ( $project eq "") {
my $project_hash_ref = $project_obj->Get_List( 'DESCRIPTION');
my ($prj,$desc);
while ( ( $prj, $desc) = each( %{$project_hash_ref})) {
delete $project_hash_ref->{$prj} unless 
$passwd_obj->Check_Project_Access( $username, $prj) 
== $TRUE; 
}
Select_Item( $IDE::Browser_Url, 'CONTROL', $title, 
$project_hash_ref);
} 
last SWITCH;
}
if ( $make_str eq 'delete') {
my @projects = split( /\t/, scalar($query->param('project')|| ''));
if ( scalar(@projects) != 0 ) { 
my $ask_for_del = $query->param('ask') || '';
if ( $ask_for_del eq 'true' ) {
my ($status, $prj);
foreach $prj ( @projects) {
$status = $project_obj->Delete( $prj);
last unless $status == $TRUE;
$message{$status} .= "Das Projekt <em>$prj</em> wurde".
" gel&ouml;scht.<br>";
}
undef $tmp_make if $status == $TRUE;
&Show_Message( $title, $message{$status}, $tmp_make);	    
}
else {
Ask_For_Projectdelete();
}
}
else {	
my $project_hash_ref = $project_obj->Get_List( 'DESCRIPTION');
Select_Item( $IDE::Ide_Url, "ACTION", $title, $project_hash_ref);
}
last SWITCH;
}
}
}
sub Project_Form {
my ($make_str,
$project,
$prjdir,
$prjdesc,
$driver_str,
$copyright,
$message) = @_;      # Uebergabeparameter
my $name_input_size = 15; 
my $copyright_input_size = 50;
my $directory_input_size = 50;
my $description_textarea_cols=50;
my $driver_select_width = 200;         
my %selected;            # Hash fuer vorausgewaehlte Felder der Auswahlliste
my $make = $query->param('make');
my $ticket = $query->param('ticket');
$project ||= '';
$prjdir ||= '';
$prjdesc ||= '';
$copyright ||= '';
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html>
<head><title>$IDE::Title</title></head>
<body bgcolor=$USER::BG_Color text=$USER::Text_Color
alink=$USER::Link_Color link=$USER::Link_Color 
vlink=$USER::Link_Color>
<font face=$USER::Font Size=$USER::Font_Size> 
<h1>Projekt $make_str</h1>
<form name="projectcontrol" action="$IDE::Ide_Url" method="get"><hr>
<input type="hidden" name="make" value="$make">
<input type="hidden" name="ticket" value="$ticket">
<blockquote>
<table bgcolor="$USER::Table_Color" border=1> <tr><td>
<table>
<tr>${FNTB}Projektname:</td>${FNTB}
<input type="text" name="project" value="$project" size="$name_input_size">
${FNTE}</tr>
<tr>${FNTB}Copyright:</td>${FNTB}
<input type="text" name="copyright" value="$copyright" 
size="$copyright_input_size">
${FNTE}</tr>
<tr>${FNTB}Projektverzeichnis:${FNTE}${FNTB}
<input type="text" name="prjdir" value="$prjdir" size="$directory_input_size" >
${FNTE}</tr>
<tr><td><br></td></tr>
<tr><td valign=top>${FONT}Projektbeschreibung:${FNTE}${FNTB}
<textarea rows=5 cols=$description_textarea_cols name="prjdesc" 
wrap=virtual>${prjdesc}</textarea>
${FNTE}</tr>
<tr><td><br></td></tr>
</table></table>
__HTML_CODE
$make_str = "\u${make_str}";
print <<__HTML_CODE;
</blockquote><p><hr>
<blockquote><input type="button" value="$make_str"
onClick="document.projectcontrol.submit()"></blockquote>
</form>
</font>    
<font face=$USER::Font size=$USER::Font_Size color=$USER::Error_Color>
__HTML_CODE
print $message,"<blink>!</blink>" if defined $message;
print "</font>";
print "</body>\n</html>";
}
sub Project_Get_Content {
my ($project,
$prjdir,
$prjdesc,
$driver_str,
$copyright,
$status,
$creator,
$project_obj) = @_;       # Uebergabeparameter
my $make = $query->param('make');
my $ticket = $query->param('ticket');
my $ip_address = $query->remote_addr();
$$prjdir = $query->param('prjdir');
$$prjdir =~ s!\\!/!g if $IDE::OS_uses_backslash;
$$prjdesc = $query->param('prjdesc');
$$prjdesc =~ s/\s+/ /g;
my @drivers = $query->param('driver');
$$driver_str = join( "\t", @drivers);
$$copyright = $query->param('copyright');
if ( $IDE::OS_has_driveletters ) {
$$status = 'WRONG_PATH_NAME', return unless $$prjdir =~ m!^[a-z]:[\\/]!i;
} else {
$$status = 'WRONG_PATH_NAME', return unless $$prjdir =~ m!^/!;
}
if ( $make eq 'prj_new') {
$$status = $project_obj->Create($project, $$prjdir, $$prjdesc,
$$driver_str, $creator, $$copyright);
}
}
sub Select_Item {
my ($action_url,
$target,
$title_str,
$item_hash) = @_;    # Uebergabeparameter
my ($select_str,         # Uberschrift der Auswahlliste
$submit_str) = split( ' ', $title_str);
$submit_str = "\u${submit_str}";
my ($set_multiple,       # Mehrfachauswahl
$select_name,        # Name des Select-Tags
$doit);              # auszufuehrendes Javascript
my $width = 200;         # Breite und 
my $size = 20;            # Hoehe des Rahmen mit der Auswahlliste
my $make = $query->param('make');       
my $ticket = $query->param('ticket');
if ( $make =~ m/usr_/) {
$select_name = 'user';
} else {
$select_name = 'project';
}
if ( $action_url eq $IDE::Browser_Url ) {
$doit="var obj = document.userselect.$select_name;\n".
"if (obj.selectedIndex != -1 ) {".	
"var prj = obj.options[obj.selectedIndex].value;\n".
"parent.ACTION.location.href='$IDE::Ide_Url?make=blank&ticket=$ticket';\n".
"parent.CONTROL.location.href=".
"'$IDE::Browser_Url?ticket=$ticket&project='+prj;}";
}
else {
$doit="if (document.userselect.${select_name}.selectedIndex != -1) ". 
"document.userselect.submit();";
}
$set_multiple = ($make =~ /_delete/) ? 'multiple' : '';
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html> <head></head>
<script language="JavaScript"> 
function doit () { ${doit} }
</script>	
<body bgcolor=$USER::BG_Color text=$USER::Text_Color
alink=$USER::Link_Color link=$USER::Link_Color 
vlink=$USER::Link_Color>
<font face=$USER::Font Size=$USER::Font_Size>
<h1>$title_str</h1><hr>
__HTML_CODE
my @values = keys %{$item_hash};
if ( scalar(@values) != 0){
print <<__HTML_CODE;
<form name="userselect" action="$action_url" method="get" target="$target">
<input type="hidden" name="make" value="$make" >
<input type="hidden" name="ticket" value="$ticket" >
<blockquote>
<table bgcolor="$USER::Table_Color" border=1> <tr><td>
<table>
<tr><td valign=top>${FONT}${select_str}name:</FONT></td>${FNTB}
<select name="$select_name" $set_multiple width=$width size=$size>
__HTML_CODE
my $prjname;         # Eintrag in der Auswahlliste fuer Projekte
my ( $value, $item);
foreach $value ( sort keys ( %{$item_hash})) {
$item = $item_hash->{$value};
$prjname = ($make =~ m/prj_/) ? "($value)" : '';
print "<option value=\"$value\"> $item $prjname\n";
}
print "</select>${FNTE}</tr></table></table></blockquote><hr>\n";
print "<blockquote><input type=\"button\" value=\"$submit_str\"\n";
print " onClick=\"doit();\"></blockquote>";
print "</form>\n";
}
else {
print "<b>keine Eintr&auml;ge enthalten</b>";
}
print "</font>\n</body>\n</html>\n";
}
sub Show_Login_Page {
my $username =           # Benutzername
$query->param('user');
$username ||= "";
my $input_width = 15;    # Breite der Eingabefelder fuer Benutzernamen und 
my $version = $IDE::Package_Version;
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html>
<head><title>$IDE::Title</title></head>
<body bgcolor=$IDE::BG_Color text=$IDE::Text_Color
alink=$IDE::Link_Color link=$IDE::Link_Color 
vlink=$IDE::Link_Color>
<img src="$IDE::Logo_Url">
<font face=$IDE::Font Size=$IDE::Font_Size>
<h1>Anmeldung</h1>
<small>spirit Server Version <b>$version</b></small><br>
<hr width="50%" align=left>
<form name="login" action="$IDE::Ide_Url" method="post">
<input type="hidden" name="make" value="login" >
<blockquote>
<table bgcolor="$IDE::Table_Color" border=1><tr><td>
<table><tr>
<td><font face=$IDE::Font Size=$IDE::Font_Size>Benutzer:</font></td><td>
<font face=$IDE::Font Size=$IDE::Font_Size>
<input type="text" name="user" value="$username" size="$input_width">
</font></td></tr>
<tr><td><font face=$IDE::Font Size=$IDE::Font_Size>Kennwort:</font></td><td>
<font face=$IDE::Font Size=$IDE::Font_Size>
<input type="password" name="passwd" size="$input_width" ></font></td>
</tr></table>
</tr></table><p>
</blockquote><hr width="50%" align=left>
<blockquote>
<input type="button" value="Anmelden" onClick="document.login.submit()">
</blockquote>
</form>
</font>    
</body>
</html>
__HTML_CODE
}
sub Show_Message {
my ($title_str,
$message,
$make,
$list_ref) = @_;     # Uebergabeparameter
my $ticket =             # Instanz der Ticketklasse
$query->param('ticket');
my $onload = '';         # Aktion beim Laden der Seite
if ( defined $make && $make eq 'onload') {
$onload = "onLoad=\"parent.CONTROL.location.href=".
"'$IDE::Ide_Url?make=menu&ticket=$ticket'\"";
undef $make;
}
print "Content-type: text/html\n\n";
print "<html>\n<head> <title>$IDE::Title</title> </head>";
if ( defined $make && ($make eq 'logout' or $make eq 'login')) {
print "<body bgcolor=$IDE::BG_Color text=$IDE::Text_Color";
print " alink=$IDE::Link_Color link=$IDE::Link_Color";
print " vlink=$IDE::Link_Color>\n";
print "<font face=$IDE::Font Size=$IDE::Font_Size>\n";
undef $make if $make eq 'logout';
$make = '' if $make eq 'login';
} 
else {
print "<body ${onload} \n";
print " bgcolor=$USER::BG_Color text=$USER::Text_Color";
print " alink=$USER::Link_Color link=$USER::Link_Color";
print " vlink=$USER::Link_Color>\n";
print "<font face=$USER::Font Size=$USER::Font_Size>\n";
}
print "<h1>$title_str</h1><hr>\n";
print "<p>$message<br>\n";
if ( defined($make)) {
print "<form name=\"login\" action=\"$IDE::Ide_Url\" ".
"method=\"post\">\n";
print "<input type=\"hidden\" name=\"make\" value=\"$make\" ><br>\n";
if ( defined( $list_ref) ) {
my ( $name, $value);
while ( ($name, $value) = each (%{$list_ref}) ) {
print "<input type=\"hidden\" name=\"$name\" ".
"value=\"$value\">\n";
}
}
print "<input type=\"button\" value =\"Wiederholen\"\n";
print " onClick=\"document.login.submit()\">";
print "</form>\n";
}    
print "</font></body></html>\n";
}
sub User_Control {
my $make = $query->param('make');
my $tmp_make = $make;    # Zwischenspeicher fuer #make
my %message = (
$Passwd::USER_ALREADY_CREATED =>
"Der Benutzer existiert bereits.<br>W&auml;hlen Sie bitte einen".
" anderen Namen f&uuml;r den Benutzer",
$Passwd::UNKNOWN_USER => 
"Der Benutzername ist dem System nicht bekannt.<br>W&auml;hlen".
" Sie bitte einen anderen Namen f&uuml;r den Benutzer",
$Passwd::NOT_INITIALIZED =>
"Das System befindet sich nicht in einem definierten Zustand",
PASSWORD_INCORRECT =>
"Die Eintr&auml;ge f&uuml;r die Kennw&ouml;rter sind ".
"unterschiedlich",
PASSWORD_NOT_VALID =>
"Sie haben vergessen ein Kennwort einzugeben",
);                       # Fehlermeldungen
my $make_str;            # Zeichenkette mit der Aktion ohne Praefix
($make_str = $make) =~ s/^usr_//;
my %make_hash = (
'new' => "anlegen",
'edit' => "bearbeiten",
'delete' => "l&ouml;schen",
);                      
my $title = "Benutzer $make_hash{$make_str}";
my $ticket_obj = new Ticket( $IDE::Ticket_File);
my $passwd_obj = new Passwd( $IDE::Passwd_File);
my $passwd;              # Kennwort
my $ticket = $query->param('ticket');
my $ip_address = $query->remote_addr();
my $username = $ticket_obj->Check($ticket, $ip_address);
if ( $username lt "0") {
&Show_Message( $error_title, $ticket_error, 'logout');
return;
}
require "$IDE::Config_Dir/${username}.pl"; &set_fonts;
$username = $query->param('user') || '';    
my $project_str;         # Projekte, an denen der Benutzer beteiligt ist
my $right_str;	     # Benutzerrechte
$passwd_obj->Get_User( $username, \$right_str, \$project_str);    
my $user_hash_ref =      # Hash mit allen dem System bekannten Benutzernamen 
$passwd_obj->Get_Userlist('USER');
my $status;              # Fehlerstatus
SWITCH: {
if ( $make_str eq 'new') {
if ( $username ne '')  {
&User_Get_Content( $passwd_obj, \$passwd, \$right_str, 
\$project_str, \$status);
if ( $status eq $TRUE) {
my $message =
"Der Benutzer <em>$username</em> wurde".
" erfolgreich angelegt.";
&Show_Message( $title, $message);
}
else {
&User_Form( $make_hash{$make_str}, $username, $right_str, 
$project_str, $message{$status});
}
}
else {
&User_Form( $make_hash{$make_str});
}
last SWITCH;
}
if ( $make_str eq 'edit') {
if ( $username eq '') {
Select_Item( $IDE::Ide_Url, 'ACTION', $title, $user_hash_ref);
}
else {
my $enter = $query->param('enter') || '';
if ( $enter eq 'true') {
&User_Get_Content( $passwd_obj, \$passwd, \$right_str, 
\$project_str, \$status);
if ( $status eq $TRUE) {
my $message =
"Die Eintragungen des Benutzers <em>$username</em>".
" wurden ge&auml;ndert";
&Show_Message( $title, $message);
}
else {
&User_Form( $make_hash{$make_str}, $username, 
$right_str, $project_str, $message{$status});
}
}
else {
&User_Form( $make_hash{$make_str}, $username, $right_str, 
$project_str);
}	
}
last SWITCH;
}
if ( $make_str eq 'delete') {
my @user = split( /\t/, scalar($query->param('user') || ''));
if ( scalar(@user) != 0 ) {
my $ask_for_del = $query->param('ask') || '';
if ( $ask_for_del eq 'true' ) {
foreach $username ( @user) {
$status = $passwd_obj->Delete_User( $username);		
my $config_obj = new Configure( $IDE::Config_File, $username);
$config_obj->Delete();
last unless $status == $TRUE;
$message{$status} .= "Der Benutzer <em>$username</em> wurde".
" gel&ouml;scht.<br>";
}
undef $tmp_make if $status == $TRUE ;
&Show_Message( $title, $message{$status}, $tmp_make);	    
}
else {
Ask_For_Userdelete();
}
}
else { 
Select_Item( $IDE::Ide_Url, 'ACTION', $title, $user_hash_ref);
}
last SWITCH;
}
}
}
sub User_Form {
my ($make_str,
$username,
$right_str,
$project_str,
$message) = @_;      # Uebergabeparameter
$username ||= '';
$right_str ||= '';
my %selected;            # Hash mit den ausgewaehlten Select-Feldern
my $make = $query->param('make');
my $ticket = $query->param('ticket');
my $select_width = 200;  # Breite der Rahmen fuer die Auswahllisten
my $input_name = 15;     # Breite des Eingabefeldes fuer den Benutzernamen
my $input_passwd = 15;   # Breite des Einagbefeldes fuer die Kennwoerter
my $ausgabe_username=''; # fettgedruckte Ausgabe des Benutzernamens
my $input_type;          # Eingabefeld oder Parameter
my $submit = $TRUE if defined $message;
$selected{user} = ($right_str =~ m/\s*USER\s*/) ? 'selected' : '';
$selected{project} = ($right_str =~ m/\s*PROJECT\s*/) ? 'selected' : '';
my @project_list = split( ',', $project_str) if defined $project_str;
my ( $prj);
foreach $prj ( @project_list) {
$selected{$prj} = 'selected';
}
my $passwd_msg = '';     # Meldung fuer Kennwortbehandlung
if ( $make =~ m/_edit/) {
$input_type = 'hidden';
$ausgabe_username = "<b>$username</b>";
$passwd_msg = "Das Kennwort kann nicht angezeigt werden.<br>".
" Ihr Kennwort wird nur ge&auml;ndert, wenn Sie ein neues eingeben.<p>";
}
else {
$input_type = 'text';
}
print "Content-type: text/html\n\n";
print <<__HTML_CODE;
<html><head><title>$IDE::Title</title></head>
<body bgcolor=$USER::BG_Color text=$USER::Text_Color
alink=$USER::Link_Color link=$USER::Link_Color 
vlink=$USER::Link_Color>
<font face=$USER::Font Size=$USER::Font_Size>
<h1>Benutzer $make_str</h1>
<form name="userctrl" action="$IDE::Ide_Url" method="get"><hr>
<input type="hidden" name="make" value="$make">
<input type="hidden" name="ticket" value="$ticket">
<input type="hidden" name="enter" value="true">
<blockquote>
<table bgcolor="$USER::Table_Color" border=1> <tr><td>
<table>
<tr>${FNTB}
Benutzername:</td>${FNTB}
<input type="$input_type" name="user" value="$username" size="$input_name">
$ausgabe_username ${FNTE}</tr><tr>${FNTB}
Kennwort des Benutzers: ${FNTE}${FNTB}
<input type="password" name="passwd1" size="$input_passwd" >
${FNTE}</tr><tr>${FNTB}
Wiederholung des Kennworts:${FNTE}${FNTB}
<input type="password" name="passwd2" size="$input_passwd" >
${FNTE}</tr><tr><td colspan=2>${FONT}
$passwd_msg</Font></tr><tr><td><br></td></tr>
<tr> <td valign=top>${FONT}
Rechte:${FNTE}${FNTB}
<select name="rights" size=5 width="$select_width" multiple>
<option value="USER" $selected{user}> Benutzerverwalter
<option value="PROJECT" $selected{project}> Projektverwalter
</select>${FNTE}</tr><tr><td valign=top>${FONT}
Projekte:${FNTE}${FNTB}
<select name="projects" size=5 width="$select_width" multiple>
__HTML_CODE
my $project_obj = new Project( $IDE::Project_File, $IDE::Driver_File);
my $project_hash_ref = $project_obj->Get_List( 'DESCRIPTION');
my ( $value, $project_dsc);
while ( ( $value, $project_dsc) = each (%{$project_hash_ref})) {
$selected{$value} ||= '';
print "<option value=\"$value\" $selected{$value}>".
"$project_dsc  ($value)";
}
$make_str = "\u${make_str}";
print <<__HTML_CODE;
</select>${FNTE}</tr></table></td></tr></table> 
</blockquote><hr><blockquote>
<input type="button" value="$make_str" onClick="document.userctrl.submit()">
</blockquote>
</form>
</font>
<font face=$USER::Font size=$USER::Font_Size color=$USER::Error_Color>
__HTML_CODE
print $message,"<blink>!</blink>" if defined $message;
print "</font></body></html>\n";
}
sub User_Get_Content {
my ($passwd_obj,
$passwd,
$right_str,
$project_str,
$status) = @_;       # Uebergabeparameter  
my $make =               # durchzufuehrende Aktion
$query->param('make');
my $username = $query->param('user');
$$passwd = $query->param('passwd1') || '';
my $passwd2 = $query->param('passwd2') || '';
my @rights = $query->param('rights');
my @projects = $query->param('projects');
$$right_str = join( ",", @rights);
$$project_str = join( ",", @projects);
if ( $$passwd ne $passwd2 ) {
$$passwd = '';
$$status = 'PASSWORD_INCORRECT';
} 
else {
SWITCH: {
if ( $make eq 'usr_edit') {
$$status =  $passwd_obj->Modify_User( $username, $$passwd, 
$$right_str, $$project_str);
last SWITCH;
} 
if ( $make eq 'usr_new'){
$$status = 'PASSWORD_NOT_VALID', return if $$passwd eq '';
$$status = $passwd_obj->Create_User( $username, $$passwd, 
$$right_str, $$project_str);
if ( $$status eq $TRUE) {
my $config_obj = new Configure( $IDE::Config_File, $username);
my ( $i, $content);
for $i ( 0 .. $#IDE::Para_Desc) {
if ( defined $IDE::Para_Desc[$i][0] ) {
eval "\$content = \$IDE::$IDE::Para_Desc[$i][0]";
$config_obj->Write( $username, $IDE::Para_Desc[$i][0], 
$content);
}
}
}
last SWITCH;
}
if ( $make eq 'cnf_password') {
$$status = 'PASSWORD_NOT_VALID', return if $$passwd eq '';
$passwd_obj->Get_User( $username, $right_str, $project_str);
$$status = $passwd_obj->Modify_User( $username, $$passwd, 
$$right_str, $$project_str);
last SWITCH;
} 
}
}
return $status;
}
