#!/usr/bin/perl
BEGIN { 
$0 =~ m!^(.*)[/\\][^/\\]+$!;    # Windows NT Netscape Workaround
chdir $1;
require "../etc/ide.cnf";		# Konfigurationsdatei fuer die IDE
unshift ( @INC, $IDE::Lib);
}
use CGI;
use Cwd;
use Ticket;
use Project;
use Lock;
use LkTyH;
use IDE_Header;
use IDE_Utils;
use strict;
my $query = new CGI;
my $ticket = $query->param('ticket');
my $th = new Ticket ($IDE::Ticket_File);
my $username;
if ( ($username = $th->Check ($ticket, $ENV{REMOTE_ADDR})) < 0 ) {
print "Content-type: text/plain\n\n";
print "Zugriffs-Fehler\n";
exit;
}
$th = undef;
require "$IDE::Config_Dir/${username}.pl";
my $event = $query->param('event');
my $project = $query->param('project');
print "Content-type: text/html\n\n" if $event ne 'download';
print "Content-type: application/x-spirit-object\n\n" if $event eq 'download';
if ( $event eq "" || $event eq "frameset" ) {
print <<__HTML_CODE;
<html><head><title>Projekt Prowser</title></head>
<frameset rows="48,*" frameborder=no border=0>
<frame name=FUNCTIONS src="$IDE::Browser_Url?ticket=$ticket&project=$project&event=functions">
<frame name=BROWSER src="$IDE::Browser_Url?ticket=$ticket&project=$project&event=show">
</frameset>
__HTML_CODE
} elsif ( $event eq "show" ) {
my $open_folders = new LkTyH ($IDE::Session_Dir.$ticket);
Project_Browser ($project, $ticket, $username,
$open_folders->{LkTyH_hash});
} elsif ( $event eq "open" ) {
my $open_folders = new LkTyH ($IDE::Session_Dir.$ticket);
my $dir = $query->param('dir');
$open_folders->{LkTyH_hash}->{$dir} = 1;
Project_Browser ($project, $ticket, $username,
$open_folders->{LkTyH_hash}, $dir);
} elsif ( $event eq "close" ) {
my $open_folders = new LkTyH ($IDE::Session_Dir.$ticket);
my $dir = $query->param('dir');
delete $open_folders->{LkTyH_hash}->{$dir};
Project_Browser ($project, $ticket, $username,
$open_folders->{LkTyH_hash}, $dir);
} elsif ( $event eq "functions" ) {
Project_Functions ($project, $ticket);
} elsif ( $event eq "edit_folder" ) {
my $dir = $query->param('dir');
Print_Header();
Edit_Folder ($project, $ticket, $dir);
Print_Footer();
} elsif ( $event eq "new_folder" ) {
my $dir = $query->param('dir');
my $folder_name = $query->param('folder_name');
New_Folder ($project, $ticket, $dir, $folder_name);
} elsif ( $event eq "ask_for_del_folder" ) {
my $dir = $query->param('dir');
my $folder_name = $query->param('folder_name');
Ask_For_Del_Folder ($project, $ticket, $dir);
} elsif ( $event eq "del_folder" ) {
my $dir = $query->param('dir');
my $folder_name = $query->param('folder_name');
Del_Folder ($project, $ticket, $dir);
} elsif ( $event eq "new_object" ) {
my $dir = $query->param('dir');
my $object_name = $query->param('object_name');
my $object_type = $query->param('object_type');
my $object_desc = $query->param('object_desc');
New_Object ($project, $ticket, $dir, $object_name,
$object_type, $object_desc, $username);
} elsif ( $event eq "ask_for_del_object" ) {
my $object = $query->param('object');
my $object_type = $query->param('object_type');
my $editor_type = $query->param('editor_type');
Ask_For_Del_Object ($project, $ticket, $object, $object_type, $editor_type);
} elsif ( $event eq "del_object" ) {
my $object = $query->param('object');
my $object_name = $query->param('object_name');
my $object_type = $query->param('object_type');
Del_Object ($project, $ticket, $object, $object_type);
} elsif ( $event eq "new_driver") {
my $driver_name = $query->param('driver_select');
my $dir = $query->param('dir');
my $status = New_Driver ($project, $ticket, $dir, $driver_name, $username);
if ( defined $status) {
Print_Header();
Edit_Folder ($project, $ticket, $dir);
Print_Footer();
}
} elsif ( $event eq "edit_properties") {
my ( $copyright, $prj_dir, $prj_desc);
my $pf = new Struct_File($IDE::Project_File);
$copyright = $pf->Read( $project, 'COPYRIGHT');
$prj_dir = $pf->Read( $project, 'DIRECTORY');
$prj_desc = $pf->Read( $project, 'DESCRIPTION');
$pf = undef;
Edit_Properties( $project, $copyright, $prj_dir, $prj_desc);
} elsif ( $event eq "save_properties") {
my ( $copyright, $prj_dir, $prj_desc);
$copyright = $query->param('copyright'); 
$prj_dir = $query->param('prjdir');
$prj_desc = $query->param('prjdesc'); 
Save_Properties( $project, $copyright, $prj_desc);
my $message = "Die Eigenschaften wurden &uuml;bernommen.";
Edit_Properties( $project, $copyright, $prj_dir, $prj_desc, $message);	
} elsif ( $event eq 'download' ) {
my $object = $query->param('object');
my $object_type = $query->param('object_type');
Download_Object ($object, $object_type);
}
exit;
sub Project_Browser {
my ($project_name, $ticket, $username, $open_folders, $jump_folder) = @_;
my $project = new Project ($IDE::Project_File, $IDE::Driver_File);
print "<html><head><title>Project Browser</title>\n";
print qq{<style type="text/css">A:visited,A:link,A:active{text-decoration:none}</style>\n};
print "</head><body bgcolor=$USER::PB_BG_Color text=$USER::PB_Text_Color\n";
print "link=$USER::PB_Link_Color vlink=$USER::PB_Link_Color\n";
print "alink=$USER::PB_Link_Color>\n";
print "<font face=$USER::Font size=$USER::Font_Size>\n";
print "<p>\n";
$project->Tree_HTML ($project_name, $open_folders,
\@IDE::Object_Sort, "$IDE::Browser_Url",
"$IDE::Driver_Url", "$IDE::Icon_Url", $ticket, $jump_folder);
print "</font>\n";
print "</body></html>\n";
}
sub Project_Functions {
my ($project_name, $ticket) = @_;
Print_Header();
print <<__HTML_CODE;
<A HREF="${IDE::Ide_Url}?make=menu&ticket=$ticket&project=$project_name" TARGET=CONTROL><IMG SRC="${IDE::Icon_Url}/spirit-logo.gif" BORDER=0 HEIGHT=24 VALIGN=top></A>
__HTML_CODE
Print_Footer();
}
sub Edit_Folder {
my ($project, $ticket, $dir, $new_folder,
$new_object, $new_object_desc, $new_object_type) = @_;
$new_object_type = '' if ! defined $new_object_type;
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $project_dir = $ph->Get_Project_Dir($project);
my $Lock = new Lock ($project, "$project_dir/src", $IDE::Session_Dir);
$Lock->Delete ($ticket);
$Lock = undef;
$ph = undef;
my $folder = $dir;
$folder =~ s!/!.!g;
my $df = new Struct_File ($IDE::Driver_File);
my $pf = new Struct_File ($IDE::Project_File);
my $used_drivers = $pf->Read ($project, "USED_DRIVERS");
my $known_drivers_ref = $df->Get_List("DRIVER_NAME");
my $dr_hash = $df->Get_List ("OBJECT_TYPES");
my $name_hash = $df->Get_List ("OBJECT_TYPE_NAMES");
my $project_src = $pf->Read( $project, 'DIRECTORY')."/src";
my $folder_path = $dir;
$folder_path =~ s!^$project/!!;
$folder_path = "$project_src/$folder_path/";
my $locked_dir = IDE_Utils::Object_Is_Dir_Locked (
$project, $folder_path, $project_src
);
print <<__HTML_CODE;
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<H3>Ordner: $folder</H3>
__HTML_CODE
if ( $locked_dir ) {
print <<__HTML_CODE;
<HR><P><FONT FACE=$USER::Font SIZE=$USER::Font_Size COLOR=red>
<B>
Dieser Ordner ist gesperrt, weil er sich im Ordner '$locked_dir' befindet
</B><P>
<HR>
__HTML_CODE
return;
}
my $project_buttons = '';
if ( $folder eq $project ) {
$project_buttons = 
qq{<P><HR WIDTH=70% ALIGN=LEFT>}.
qq{<FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{<B>Projektfunktionen</B><P>}.
qq{<BLOCKQUOTE>}.
qq{<INPUT TYPE=BUTTON VALUE=" Projekteigenschaften Editieren "}.
qq{onClick="document.Ordner.event.value='edit_properties';}.
qq{document.Ordner.submit()"><P>}.
qq{<INPUT TYPE=BUTTON VALUE=" Projekt komplett neu übersetzen "}.
qq{onClick="document.Ordner.event.value='make_all';}.
qq{document.Ordner.action='$IDE::Make_All_Url';}.
qq{document.Ordner.submit()">}.
qq{</FONT></BLOCKQUOTE>};
}
my $driver_select;
my $driver_section = '';	
my $driver;
foreach $driver ( split( '\t',$used_drivers) ) {
delete $known_drivers_ref->{$driver};
}
if ( 0 and $folder eq $project and scalar( keys(%{$known_drivers_ref})) != 0) {
my $dname;
$driver_select = "<SELECT NAME=driver_select>";		
while ( ($driver,$dname) = (each %{$known_drivers_ref}) ) {
$driver_select .= "<OPTION VALUE=$driver> $dname ($driver)\n";
}
$driver_select .= "</SELECT>\n";
$driver_section .= 
qq{<HR WIDTH=75% ALIGN=LEFT>\n}.
qq{<B>Neuen Treiber in das Projekt einbinden</B>\n}.
qq{<P><br><FORM NAME=Driver METHOD=POST ACTION="$IDE::Browser_Url">\n}.
qq{<INPUT TYPE=HIDDEN NAME=ticket VALUE="$ticket">\n}.
qq{<INPUT TYPE=HIDDEN NAME=project VALUE="$project">\n}.
qq{<INPUT TYPE=HIDDEN NAME=dir VALUE="$dir">\n}.
qq{<INPUT TYPE=HIDDEN NAME=event VALUE=new_driver>\n}.
qq{<BLOCKQUOTE><TABLE BGCOLOR=$USER::Table_Color BORDER=1>\n}.
qq{<TR><TD VALIGN=TOP> <TABLE>\n}.
qq{<TR><TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>\n}.
qq{Treiber:</FONT></TD><TD ALIGN=RIGHT>}.
qq{<FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{$driver_select</FONT></TD></TR><TR><TD ALIGN=RIGHT COLSPAN=2>}.
qq{<FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{<INPUT TYPE=BUTTON VALUE=" Treiber einbinden "}.
qq{onClick="document.Driver.submit()"></FONT></TD></TR></TABLE>\n}.
qq{</TD></TR></TABLE></FORM></BLOCKQUOTE>\n};
}
print $driver_section;
my $tmp_used_drivers = "\t".$used_drivers."\t";
my $type_select = "<SELECT NAME=object_type>\n";
my $type_list;
while ( ($driver, $type_list) = each (%{$dr_hash}) ) {
next if $tmp_used_drivers !~ /\t$driver\t/;
my ($type, $name, @driver_names);
@driver_names = split ("\t", $name_hash->{$driver});
foreach $type (split("\t", $type_list)) {
$name = shift @driver_names;
next if $type eq "${driver}-driver-config";
my $s;
$s = ("$driver:$type" eq $new_object_type) ? "SELECTED" : "";
$type_select .= "<OPTION VALUE=$driver:$type $s> $name\n";
}
}
$type_select .= "</SELECT>\n";
if ( $used_drivers ne '' ) { 
print <<__HTML_CODE;
<HR WIDTH=75% ALIGN=LEFT>
<B>Neues Objekt in diesem Ordner anlegen</B>
<P>
</FONT>
<FORM NAME=Objekt METHOD=POST ACTION="$IDE::Browser_Url">
<INPUT TYPE=HIDDEN NAME=ticket VALUE="$ticket">
<INPUT TYPE=HIDDEN NAME=project VALUE="$project">
<INPUT TYPE=HIDDEN NAME=dir VALUE="$dir">
<INPUT TYPE=HIDDEN NAME=event VALUE=new_object>
<BLOCKQUOTE>
<TABLE BGCOLOR=$USER::Table_Color BORDER=1>
<TR><TD VALIGN=TOP>
<TABLE>
<TR><TD>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Objekttyp: 
</FONT>
</TD><TD>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
$type_select
</FONT>
</TD></TR>
<TR><TD>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Name:
</FONT>
</TD><TD>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<INPUT TYPE=TEXT NAME=object_name VALUE="$new_object" SIZE=20 MAXLENGTH=20>
</FONT>
</TD></TR>
<TR><TD VALIGN=TOP>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Beschreibung:
</FONT>
</TD><TD>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<TEXTAREA NAME=object_desc ROWS=4 COLS=40 
WRAP=virtual>$new_object_desc</TEXTAREA>
</FONT>
</TD></TR>
</TABLE>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<DIV ALIGN=RIGHT>
<INPUT TYPE=BUTTON VALUE=" Objekt anlegen "
onClick="document.Objekt.submit()">
</FONT>
</TR></TD>
</TABLE>
</BLOCKQUOTE>
</FORM>
<P>
__HTML_CODE
}
print <<__HTML_CODE;
<HR WIDTH=75% ALIGN=LEFT>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<B>Neuen Ordner anlegen</B>
<P>
<FORM NAME=Ordner METHOD=POST ACTION="$IDE::Browser_Url">
<INPUT TYPE=HIDDEN NAME=ticket VALUE="$ticket">
<INPUT TYPE=HIDDEN NAME=project VALUE="$project">
<INPUT TYPE=HIDDEN NAME=dir VALUE="$dir">
<INPUT TYPE=HIDDEN NAME=event VALUE=new_folder>
<BLOCKQUOTE>
<TABLE BGCOLOR=$USER::Table_Color BORDER=1>
<TR><TD>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Name:
<INPUT TYPE=TEXT NAME=folder_name VALUE="$new_folder" SIZE=20 MAXLENGTH=20>
<DIV ALIGN=RIGHT>
<INPUT TYPE=BUTTON VALUE=" Ordner anlegen "
onClick="document.Ordner.submit()">
</FONT>
</TD></TD>
</TABLE>
</BLOCKQUOTE>
$project_buttons
</FORM>
__HTML_CODE
return if $folder !~ /\./;	# Wenn kein . drin, dann handelt
print <<__HTML_CODE;
<P>
<HR WIDTH=75% ALIGN=LEFT>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<B>Diesen Ordner löschen</B>
<P>
<FORM NAME=Loeschen METHOD=POST ACTION="$IDE::Browser_Url">
<INPUT TYPE=HIDDEN NAME=ticket VALUE="$ticket">
<INPUT TYPE=HIDDEN NAME=project VALUE="$project">
<INPUT TYPE=HIDDEN NAME=dir VALUE="$dir">
<INPUT TYPE=HIDDEN NAME=event VALUE=ask_for_del_folder>
<BLOCKQUOTE>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<INPUT TYPE=BUTTON VALUE=" Ordner löschen "
onClick="document.Loeschen.submit()">
</FONT>
</BLOCKQUOTE>
</FORM>
__HTML_CODE
}
sub New_Folder {
my ($project, $ticket, $dir, $folder_name) = @_;
my $error_msg;
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
$error_msg = $ph->Add_Folder ($project, $dir, $folder_name);
$ph = undef;
if ( defined $error_msg ) {
Print_Header();
Edit_Folder ($project, $ticket, $dir, $folder_name);
print "<HR WIDTH=75% ALIGN=LEFT>\n";
print "<FONT FACE=$USER::Font SIZE=$USER::Font_Size COLOR=$USER::Error_Color>\n";
print "$error_msg<P>\n";
print "</FONT>\n";
Print_Footer();
} else {
Print_Header(
"parent.CONTROL.BROWSER.location.href=".
"'$IDE::Browser_Url?ticket=$ticket&project=$project&".
"event=show'");
Edit_Folder ($project, $ticket, $dir);
print "<HR WIDTH=75% ALIGN=LEFT>\n";
print "<FONT FACE=$USER::Font SIZE=$USER::Font_Size>\n";
$dir =~ s!/!.!g;
print "Der Ordner '$folder_name' wurde unter ",
"'$dir' angelegt.<P>\n";
print "</FONT>\n";
Print_Footer();
}
}
sub Ask_For_Del_Folder {
my ($project, $ticket, $dir) = @_;
my $folder = $dir;
$folder =~ s!/!.!g;
my $message;
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $obj_path = $ph->Get_Object_Path ($folder);
opendir (CHECKDIR, $obj_path) or die "opendir $obj_path";
my @checkdir = grep ( !/^\.\.?/, readdir CHECKDIR );
closedir CHECKDIR;
my $delete_button = <<__HTML;
<INPUT TYPE=BUTTON VALUE=" Löschen "
onClick="document.Frage.event.value='del_folder';
document.Frage.submit()">
__HTML
if ( scalar @checkdir > 0 ) {
$message = "Der Ordner enthält noch Daten!<BR>".
"Sie können den Ordner erst löschen, wenn diese ".
"entfernt wurden\n";
$delete_button = "";
} else {
$message = "Der Ordner enthält keine Daten.";
}
Print_Header();
print <<__HTML_CODE;
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<H3>Ordner: $folder</H3>
<HR WIDTH=75% ALIGN=LEFT>
<B>Soll dieser Ordner wirklich gelöscht werden?</B>
<P>
</FONT>
<FORM NAME=Frage METHOD=POST ACTION="$IDE::Browser_Url">
<INPUT TYPE=HIDDEN NAME=ticket VALUE="$ticket">
<INPUT TYPE=HIDDEN NAME=project VALUE="$project">
<INPUT TYPE=HIDDEN NAME=dir VALUE="$dir">
<INPUT TYPE=HIDDEN NAME=event VALUE=edit_folder>
<BLOCKQUOTE>
<TABLE BGCOLOR=$USER::Table_Color BORDER=1>
<TR><TD>
<TABLE><TR><TD COLSPAN=2 ><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
$message</FONT></TD></TR>
<TR><TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
</FONT></TD><TD ALIGN=RIGHT><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
$delete_button
<INPUT TYPE=BUTTON VALUE=" Abbrechen "
onClick="document.Frage.submit()">
</FONT></TD></TR>
</TABLE>
</TD></TR>
</TABLE>
</BLOCKQUOTE>
</FORM>
<P>
__HTML_CODE
}
sub Del_Folder {
my ($project, $ticket, $dir) = @_;
my $folder = $dir;
$folder =~ s!/!.!g;
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $success = $ph->Del_Folder ($project, "$dir");
my $error_msg;
if ( $success < 0)  {
$error_msg = "Es ist ein Systemfehler aufgetreten!\n";
}
if ( defined $error_msg ) {
Print_Header();
Edit_Folder ($project, $ticket, $dir, $folder);
print "<HR WIDTH=75% ALIGN=LEFT>\n";
print "<FONT FACE=$USER::Font SIZE=$USER::Font_Size COLOR=$USER::Error_Color>\n";
print "$error_msg<P>\n";
print "</FONT>\n";
Print_Footer();
} else {
Print_Header(
"parent.CONTROL.BROWSER.location.href=".
"'$IDE::Browser_Url?ticket=$ticket&project=$project&".
"event=show'");
print <<__HTML_CODE;
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<H3>Ordner: $folder</H3>
<HR WIDTH=75% ALIGN=LEFT>
<B>Der Ordner wurde gelöscht!</B>
<P>
</FONT>
__HTML_CODE
Print_Footer();
}
}
sub New_Object {
my ($project, $ticket, $dir, $object_name,
$object_type, $object_desc, $username) = @_;
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $error_msg = $ph->Add_Object
($project, $dir, $object_name, $object_type,
$object_desc, $username);
if ( defined $error_msg ) {
Print_Header();
Edit_Folder ($project, $ticket, $dir, undef,
$object_name, $object_desc, $object_type);
print "<HR WIDTH=75% ALIGN=LEFT>\n";
print "<FONT FACE=$USER::Font SIZE=$USER::Font_Size COLOR=$USER::Error_Color>\n";
print "$error_msg<P>\n";
print "</FONT>\n";
Print_Footer();
} else {
my $object = "$dir.$object_name";
$object_type =~ s/(.*)://;
my $driver = $1;
$object =~ s!/!.!g;
Print_Header(
"parent.CONTROL.BROWSER.location.href=".
"'$IDE::Browser_Url?ticket=$ticket&project=$project&".
"event=show';".
"parent.ACTION.location.href=".
"'$IDE::Driver_Url/$driver/driver.cgi?ticket=$ticket&".
"project=$project&object=$object&object_type=$object_type&".
"event=edit';");
Print_Footer();
}
}
sub Ask_For_Del_Object {
my ($project, $ticket, $object_name, $object_type, $editor_type) = @_;
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $driver = $ph->{object_types}->{$object_type};
$ph = undef;
$editor_type = 'properties' if $editor_type eq 'property';
$editor_type = 'edit' if $editor_type eq 'content';
my $old_request_method = $main::ENV{REQUEST_METHOD};
my $old_query_string = $main::ENV{QUERY_STRING};
$main::ENV{REQUEST_METHOD} = 'GET';
$main::ENV{QUERY_STRING} = 
"event=ask_for_delete&ticket=$ticket&object=$object_name&".
"object_type=$object_type&project=$project";
my $old_dir = cwd();
chdir "$IDE::Driver_Dir/$driver";
open ( DRVR, "./driver.cgi 2>&1 |");
my $driver_output;
while (<DRVR>) {
$driver_output .= $_;
}
close( DRVR) or die "Systemfehler bei internem CGI-Aufruf: ".
"$IDE::Driver_Dir/$driver/driver.cgi: $driver_output";
chdir $old_dir;
$main::ENV{REQUEST_METHOD} = $old_request_method;
$main::ENV{QUERY_STRING} = $old_query_string;
Print_Header();
print <<__HTML_CODE;
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<H3>Objekt: $object_name ($object_type)</H3>
<HR WIDTH=75% ALIGN=LEFT>
$driver_output
<P><B>Soll dieses Objekt wirklich gelöscht werden?</B>
<P>
</FONT>
<FORM NAME=Frage METHOD=POST ACTION="$IDE::Browser_Url">
<INPUT TYPE=HIDDEN NAME=ticket VALUE="$ticket">
<INPUT TYPE=HIDDEN NAME=project VALUE="$project">
<INPUT TYPE=HIDDEN NAME=object VALUE="$object_name">
<INPUT TYPE=HIDDEN NAME=object_type VALUE="$object_type">
<INPUT TYPE=HIDDEN NAME=event VALUE="$editor_type">
<BLOCKQUOTE>
<TABLE BGCOLOR=$USER::Table_Color BORDER=1>
<TR><TD>
<TABLE><TR><TD COLSPAN=2 ><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
</FONT></TD></TR>
<TR><TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<INPUT TYPE=BUTTON VALUE=" Löschen "
onClick="document.Frage.event.value='del_object';
document.Frage.submit()">
</FONT></TD><TD ALIGN=RIGHT><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<INPUT TYPE=BUTTON VALUE=" Abbrechen "
onClick="document.Frage.action='$IDE::Driver_Url/$driver/driver.cgi';
document.Frage.submit()">
</FONT></TD></TR>
</TABLE>		    
</TD></TR>
</TABLE>
</BLOCKQUOTE>
</FORM>
<P>
__HTML_CODE
}
sub Del_Object {
my ($project, $ticket, $object_name, $object_type) = @_;
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $driver = $ph->{object_types}->{$object_type};
$ph = undef;	# wegen Driver Systemaufruf: sonst Deadlock
my $old_request_method = $main::ENV{REQUEST_METHOD};
my $old_query_string = $main::ENV{QUERY_STRING};
$main::ENV{REQUEST_METHOD} = 'GET';
$main::ENV{QUERY_STRING} = 
"event=delete&ticket=$ticket&object=$object_name&".
"object_type=$object_type&project=$project";
my $old_dir = cwd();
chdir "$IDE::Driver_Dir/$driver";
open ( DRVR, "./driver.cgi 2>&1 |");
my $driver_output;
while (<DRVR>) {
$driver_output .= $_;
}
close( DRVR) or die "Systemfehler bei internem CGI-Aufruf: $!\n";
chdir $old_dir;
$main::ENV{REQUEST_METHOD} = $old_request_method;
$main::ENV{QUERY_STRING} = $old_query_string;
$ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $success = $ph->Del_Object ($project, $object_name, $object_type);
my $error_msg;
if ( $success < 0)  {
$error_msg = "Es ist ein Systemfehler aufgetreten!\n";
}
if ( defined $error_msg ) {
Print_Header();
print <<__HTML_CODE;
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<H3>Objekt: $object_name ($object_type)</H3>
<HR WIDTH=75% ALIGN=LEFT>
<B>Das Objekt konnte nicht gelöscht werden. $error_msg</B>
<P>
</FONT>
__HTML_CODE
Print_Footer();
} else {
Print_Header(
"parent.CONTROL.BROWSER.location.href=".
"'$IDE::Browser_Url?ticket=$ticket&project=$project&".
"event=show'");
print <<__HTML_CODE;
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<H3>Objekt: $object_name ($object_type)</H3>
<HR WIDTH=75% ALIGN=LEFT>
<B>Das Objekt wurde gelöscht!</B>
<P>
</FONT>
__HTML_CODE
Print_Footer();
my $project_dir = $ph->Get_Project_Dir($project);
my $Lock = new Lock ($project, "$project_dir/src", $IDE::Session_Dir);
$Lock->Delete ($ticket);
}
}
sub New_Driver {
my ($project,
$ticket,
$dir,
$driver_name,
$username) = @_;
my $df = new Struct_File ($IDE::Driver_File);
my $object_types = $df->Read ($driver_name, "OBJECT_TYPES");
if ( $object_types =~ m/${driver_name}-driver-config/) {
New_Object ($project, $ticket, $dir, "$driver_name-Konfiguration",
"$driver_name:${driver_name}-driver-config", '', $username);
return undef;
}
else {
my $pf = new Struct_File ($IDE::Project_File);
my $used_drivers = $pf->Read ($project, "USED_DRIVERS");
$used_drivers .= "\t$driver_name";
$used_drivers =~ s/^\t//;
$pf->Write ($project, "USED_DRIVERS", $used_drivers);   
return 1;
}
}
sub Edit_Properties {
my ($project,
$copyright,
$prj_dir,
$prj_desc,
$message) = @_;
my $name_input_size = 15; 
my $copyright_input_size = 50;
my $description_textarea_cols=50;
Print_Header();
print <<__HTML_CODE;
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<H1>Projekt-Eigenschaften</H1>
<FORM NAME="projectcontrol" ACTION="$IDE::Browser_Url" METHOD="POST"><HR>
<INPUT TYPE="HIDDEN" NAME="project" VALUE="$project">
<INPUT TYPE="HIDDEN" NAME="ticket" VALUE="$ticket">
<INPUT TYPE="HIDDEN" NAME="event" VALUE=save_properties>	
<INPUT TYPE="HIDDEN" NAME="prjdir" VALUE="$prj_dir">	
<BLOCKQUOTE>
<TABLE BGCOLOR="$USER::Table_Color" BORDER=1> <TR><TD>
<TABLE>
<TR><TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>Projektname:</TD>
<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<B>$project</B>
</FONT></TD></TR>
<TR><TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>Copyright:</TD>
<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<INPUT TYPE="TEXT" NAME="copyright" VALUE="$copyright" 
SIZE="$copyright_input_size">
</FONT></TD></TR>
<TR><TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>Projektverzeichnis:
</FONT></TD>
<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<B>$prj_dir</B>
</FONT></TD></TR>
<TR><TD><BR></TD></TR>
<TR><TD VALIGN=TOP>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>Projektbeschreibung:</FONT></TD>
<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<TEXTAREA ROWS=5 COLS=$description_textarea_cols NAME="prjdesc" 
WRAP=VIRTUAL>${prj_desc}</TEXTAREA>
</FONT></TD></TR>
<TR><TD><BR></TD></TR>
</TABLE></TABLE>
</BLOCKQUOTE><HR><BLOCKQUOTE>
<INPUT TYPE="BUTTON" VALUE=" Speichern " 
ONCLICK="document.projectcontrol.submit()">
</BLOCKQUOTE>
</FORM>
$message
</FONT>
__HTML_CODE
Print_Footer();
}
sub Save_Properties {
my ($project,
$copyright,
$prj_desc) = @_;
my $pf = new Struct_File($IDE::Project_File);
$pf->Write( $project, 'COPYRIGHT', $copyright);
$pf->Write( $project, 'DESCRIPTION', $prj_desc);
$pf = undef;
}
sub Download_Object {
my ($object, $object_type) = @_;
my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
my $object_path = $ph->Get_Object_Path ($object);
$object_path .= ".$object_type";
open (IDE_OBJECT_READ, $object_path);
my $header = new IDE_Header ( *IDE_OBJECT_READ );
if ( $IDE_Header::init_status != 1 ) {
print "Die Objektdatei '$object' -> $object_path ist fehlerhaft: ".
"$IDE_Header::init_status!";
} else {
while (<IDE_OBJECT_READ>) {
if ( $IDE::CLIENT_OS == 0 ) {
s/\r$//;
} else {
s/\r$//;
s/\n$//;
$_ .= "\r\n";
}
print $_;
}
}
close IDE_OBJECT_READ;
}
sub Print_Header {
local ($main::__header_printed);
my ($onload) = @_;
return if $main::__header_printed;
if ( $onload ne '' ) {
$onload = qq{onLoad="$onload"};
}
print <<__HTML_CODE;
<HTML><HEAD><TITLE>spirit</TITLE></HEAD>
<BODY BGCOLOR=$USER::BG_Color TEXT="$USER::Text_Color"
ALINK="$USER::Link_Color" VLINK="$USER::Link_Color"
LINK="$USER::Link_Color" $onload>
__HTML_CODE
$main::__header_printed = 1;
}
sub Print_Footer {
local ($main::__footer_printed);
return if $main::__footer_printed;
print "</BODY></HTML>\n";
$main::__footer_printed = 1;
}
