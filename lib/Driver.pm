package Driver;
use Ticket;
use Passwd;
use Project;
use IDE_Header;
use Configure;
use Depend;
use IDE_Utils;
use Lock;
use CGI;
use File::Copy;              # Modul zum Kopieren von Dateien oder Dateihandles
use Text::Wrap;              # Modul mit Textformatfunktionen
use FileHandle;              # Objektmethoden fuer Dateihandles bereitstellen
use strict;
my $initial_version = "0.0.0.0";
sub new {
my $type = shift;
my ($driver_name, $debug) = @_;
my $query;
if ( $debug ) {
if ( open (DEBUG, "$IDE::OS_temp_dir/form.txt") ) {
$query = new CGI (\*DEBUG);
close DEBUG;
} else {
$query = new CGI;
}
} else {
$query = new CGI;
}
my $myurl = $query->url();
$myurl =~ s!^http://[^/]+!!;		# Workaraound um Systems Bug!
my $ticket  = $query->param('ticket');
my $project = $query->param('project');
my $object = $query->param('object');
my $object_type = $query->param('object_type');
my $object_type_desc;
my $event = $query->param('event');
if ( ($object eq '') || ($object_type eq '') || 
($event eq '')  || ($project eq '') || ($ticket eq '') ) {
Print_Error_Message("Unvollstaendiger Aufruf. Es fehlen Parameter!");
}
my $th = new Ticket ($IDE::Ticket_File);
my $username = $th->Check ($ticket, $ENV{REMOTE_ADDR});
if ( $username eq $Ticket::TICKET_UNKNOWN or
$username eq $Ticket::WRONG_IP ) {
Print_Error_Message("Ticket-Zugriffs-Fehler");
}
require "$IDE::Config_Dir/${username}.pl";
$th = undef;
my $passwd = new Passwd ($IDE::Passwd_File);
if ( ! 1 == $passwd->Check_Project_Access ($username, $project) ) {
Print_Error_Message("Projekt-Zugriffs-Fehler! Sie haben kein Recht\n".
"auf dieses Projekt zuzugreifen!");
}
$passwd = undef;
my $pf = new Struct_File ($IDE::Project_File);
my $project_src_hash = $pf->Get_List ("DIRECTORY");
$pf = undef;
my $project_dir = $project_src_hash->{$project};
my $new_file_path;
if ( $IDE::cvs ) {
$new_file_path = $object;
$new_file_path =~ s/^$project\././;
$new_file_path =~ s!\.!/!g;
$new_file_path =~ s!(.*)/([^/]+)$!$1/.new_$2!;
$new_file_path = "$project_dir/src$new_file_path.$object_type";
$initial_version = "42.0.0.1" if -f $new_file_path;
unlink $new_file_path if $event eq 'save';
}
my $foo;
foreach $foo ( keys %{$project_src_hash} ) {
$project_src_hash->{$foo} .= "/src";
}
my $df = new Struct_File ($IDE::Driver_File);
my $object_types = $df->Read ($driver_name, "OBJECT_TYPES");	
my $object_types_desc = $df->Read ($driver_name, "OBJECT_TYPE_NAMES");
my $driver_tags = $df->Read ($driver_name, "HEADER_TAGS");
$df = undef;
my @object_types_list = split( '\t', $object_types);
my @object_types_desc_list = split( '\t', $object_types_desc);
while ( (shift(@object_types_list)) ne $object_type) {
shift @object_types_desc_list;
}
$object_type_desc = shift @object_types_desc_list;
my $editor_type = '';
if ( $event eq 'save') {
$editor_type = $query->param('editor_type');
}
my $driver_parameter_url =
"ticket=$ticket&project=$project&object=$object&".
"object_type=$object_type";
my $driver_parameter_form =
qq {<INPUT TYPE=HIDDEN NAME=ticket VALUE="$ticket">\n}.
qq {<INPUT TYPE=HIDDEN NAME=project VALUE="$project">\n}.
qq {<INPUT TYPE=HIDDEN NAME=object VALUE="$object">\n}.
qq {<INPUT TYPE=HIDDEN NAME=object_type VALUE="$object_type">\n};
my $font = "<FONT FACE=$USER::Font SIZE=$USER::Font_Size>";
my $error_font = 
"<FONT FACE=$USER::Font SIZE=$USER::Font_Size COLOR=$USER::Error_Color>";
my $driver_sys_dir = $IDE::Driver_System_Dir."/$driver_name";
my $driver_src_dir = $project_dir."/src/.$driver_name";
if ( ! -d $driver_src_dir ) {
mkdir $driver_src_dir, 0775;
}
my $self = {
"driver" => $driver_name,
"project_dir" => $project_dir,
"query" => $query,
"url" => $myurl,
"driver_parameter_url" => $driver_parameter_url,
"driver_parameter_form" => $driver_parameter_form,
"driver_tags" => $driver_tags,
"ticket" => $ticket,
"username" => $username,
"project" => $project,
"object_type_desc" => $object_type_desc,
"font" => $font,
"error_font" => $error_font,
"project_src_hash" => $project_src_hash,
"driver_sys_dir" => $driver_sys_dir,
"driver_src_dir" => $driver_src_dir,
"editor_type" => $editor_type,
"lock_info" => undef
};
$self = bless $self, $type;
$self->Reinit_With_Object ($object, $object_type);
my $header = $self->{header};
if ( ($event eq 'edit' or $event eq 'versions') and 
$header->Get_Tag ("OBJECT_VERSION") eq $initial_version ) {
$event = 'new_object';
}
if ( $event eq 'edit' or $event eq 'show_version' or 
$event eq 'versions' or $event eq 'properties' or
$event eq 'preprocess' or $event eq 'new_object' )	{
my $lock_dir = IDE_Utils::Object_Is_Dir_Locked(
$self->{project},
$self->{object_path},
"$self->{project_dir}/src"
);
if ( $lock_dir ) {
$self->{lock_info}->{lock_dir} = $lock_dir;
} else {
my $Lock = new Lock (
$self->{project},
"$self->{project_dir}/src",
$IDE::Session_Dir
);
my $force = $query->param('override_lock');
my $success = $Lock->Set ($ticket, $username, $object, $force);
if ( not $success ) {
my ($lock_ticket, $lock_username, $lock_time) =
$Lock->Get_Object_Info ($object);
$self->{lock_info}->{username} = $lock_username;
$self->{lock_info}->{"time"} =
IDE_Utils::Format_Timestamp($lock_time);
} else {
$self->{lock_info} = undef;
}
}
}
if ( $event eq 'save' ) {
my $Lock = new Lock (
$self->{project},
"$self->{project_dir}/src",
$IDE::Session_Dir
);
my ($lock_ticket, $lock_username, $lock_time) =
$Lock->Get_Object_Info ($object);
if ( defined $lock_ticket and $lock_ticket ne $ticket ) {
$self->{lock_info}->{username} = $lock_username;
$self->{lock_info}->{"time"} =
IDE_Utils::Format_Timestamp($lock_time);
$self->{lock_info}->{data_lost} = 1;
$event = 'edit' if $editor_type eq 'content';
$event = 'versions' if $editor_type eq 'versions';
$event = 'properties' if $editor_type eq 'property';
}
}
if ( $event eq 'save' and $object_type =~ m/driver-config$/
and $header->Get_Tag ("OBJECT_VERSION") eq $initial_version ) {
$event = 'driver_install';
my $pf = new Struct_File ($IDE::Project_File);
my $used_drivers = $pf->Read ($project, "USED_DRIVERS");
$used_drivers .= "\t$driver_name";
$used_drivers =~ s/^\t//;
$pf->Write ($project, "USED_DRIVERS", $used_drivers);
$pf = undef;	    
}
$self->{event} = $event;
return bless $self, $type;
}
sub Reinit_With_Object {
my $self = shift;
my ($object, $object_type) = @_;
my $project = $self->{project};
my $project_dir = $self->{project_dir};
my $object_path = $object;
$object_path =~ s/^$project\.//;
$object_path =~ s!\.!/!g;
$object_path = "$project_dir/src/$object_path.$object_type";
$self->{object} = $object;
$self->{object_type} = $object_type;
$self->{object_path} = $object_path;
open (IDE_OBJECT_READ, $object_path);
select IDE_OBJECT_READ;
if ( $object_type eq 'cipp-img' ) {
binmode IDE_OBJECT_READ;
}
$| = 1;
select STDOUT;
my $header = new IDE_Header ( *IDE_OBJECT_READ );
if ( $IDE_Header::init_status != 1 ) {
Print_Error_Message("Die Objektdatei '$object' ist fehlerhaft: ".
"$IDE_Header::init_status!");
}
$self->{header} = $header;
$self->{filehandle} = \*IDE_OBJECT_READ;
return;
}
sub Prepare_Save {
my $self = shift;
my $object_version = $self->{header}->Get_Tag ("OBJECT_VERSION");
my $object_name = $self->{header}->Get_Tag ("OBJECT_NAME");
my $object_type = $self->{header}->Get_Tag ("OBJECT_TYPE");
my ($description, $copyright);
if ( $self->{editor_type} eq 'content' ) {
$description = $self->{header}->Get_Tag ("DESCRIPTION");
$copyright = $self->{header}->Get_Tag ("COPYRIGHT");
} else {
$description = $self->{query}->param('prop_description');
$copyright = $self->{query}->param('prop_copyright');
}
my $modification_history =
$self->{header}->Get_Tag ("MODIFICATION_HISTORY");
$self->{header}->Set_Free ($self->{filehandle});
$self->{header} = undef;
my $read_fh = $self->{filehandle};
close $read_fh;
my $old_object_file = $self->Move_Old_Object($object_version);
my $new_object_version = $object_version;
my $object_modification = $self->{query}->param('object_modification') || '';
my $modification_date = IDE_Utils::Get_Timestamp();
if ( $object_modification ne "" and $self->{editor_type} ne 'version') {
$new_object_version =~ s/([^\.]+)\.[^\.]+$//;
my $release = $1;
$new_object_version .= ( ++$release . ".0" );
} 
else {
$new_object_version =~ s/([^\.]+)$//;
my $release = $1;
$new_object_version .= ++$release;
}
if ( $object_modification ne "") {
$Text::Wrap::columns -= $IDE_Header::spaces;
eval { $object_modification = wrap ( '', '', $object_modification); };
$modification_history .= "\n\n$new_object_version $modification_date ".
"$self->{username}\n$object_modification";
}
my $header = new IDE_Header (undef, $self->{driver_tags});
$header->Put_Tag ("OBJECT_VERSION", $new_object_version);
$header->Put_Tag ("OBJECT_NAME", $object_name);
$header->Put_Tag ("OBJECT_TYPE", $object_type);
$header->Put_Tag ("DESCRIPTION", $description);
$header->Put_Tag ("COPYRIGHT", $copyright );
$header->Put_Tag ("MODIFICATION_HISTORY", $modification_history);
$header->Put_Tag ("LAST_MODIFY_BY", $self->{username});
$header->Put_Tag ("LAST_MODIFY_DATE", $modification_date);
$self->{header} = $header;
return 1;
}
sub Move_Old_Object {
my $self = shift;
my $object_version = shift;
my $version_dir;
($version_dir = $self->{object_path}) =~ s!([^/]+)$!.$1!;	
my $object_name = $1;
unless ( -e $version_dir ) {
my $error;
$error = mkdir( $version_dir, 0775);
if ( $error == 0) {
print STDERR "Move_old_Object: can't mkdir\n";
return;
}
}
my $version_file = "$version_dir/$object_name-$object_version";
copy ($self->{object_path}, $version_file) or 
Print_Error_Message("Datei konnte nicht kopiert werden!");
}
sub HTML_Text_Escape {
my $self = shift;
my ($text) = @_;
$$text =~ s/&/&amp;/g;
$$text =~ s/</&lt;/g;
$$text =~ s/>/&gt;/g;
$$text =~ s/\"/&quot;/g;
}
sub Print_Editor_Header {
my $self = shift;
my ($editor_type, $enc_type,
$modification_bar, $edit_button_text, $save_disable) = @_;
$editor_type = '' if ! defined $editor_type;
$enc_type = "application/x-www-form-urlencoded" if ! defined $enc_type;
$modification_bar ||= '';
$edit_button_text ||= 'Editieren';
my $font = $self->{font};
my $color = $USER::Inactive_Color;
my $ticket = $self->{ticket};
my $project= $self->{project};
my $object = $self->{object};
my $object_type = $self->{object_type};
my $object_type_desc = $self->{object_type_desc};
my $object_version = $self->{header}->Get_Tag ('OBJECT_VERSION');
my $url = $self->{url};
my ($back_button, $type_field, $modification_input, 
$type_field_value, $restore, $colspan);
$restore = '';
$modification_input = '';
$colspan = ( $self->{header}->Get_Tag ('DESCRIPTION') ne '') ? 3 : 2;
my $lock_message = '';
my $delete_disable = 0;
if ( defined $self->{lock_info} ) {
$save_disable = 1;
$delete_disable = 1;
my $lost_message = '';
if ( $self->{lock_info}->{data_lost} ) {
$lost_message = "<B>ACHTUNG!</B> Ihre letzten Änderungen an dem ".
"Objekt sind verloren. Sie sehen die letzte ".
"Version des Objektes!<BR>\n";
}
if ( not $self->{lock_info}->{lock_dir} ) {
my $unlock_button = qq{
&nbsp;&nbsp;&nbsp;<INPUT TYPE=BUTTON VALUE=" Sperre aufheben "
onClick="document.IDE_Functions.override_lock.value=1;
document.IDE_Functions.event.value='$self->{event}';
document.IDE_Functions.submit()">
};
my $time = $self->{lock_info}->{"time"};
$lock_message = qq{<TR><TD VALIGN=TOP COLSPAN=$colspan BGCOLOR=red>}.
qq{<FONT FACE=$USER::Font SIZE=$USER::Font_Size COLOR=white>}.
qq{$lost_message<B>Hinweis: </B>}.
qq{Dieses Objekt ist derzeit in Bearbeitung von Benutzer: <B>}.
$self->{lock_info}->{username}.
qq{</B>. Das Objekt ist gesperrt seit: <B>$time</B>\n}.
qq{$unlock_button</FONT></TD></TR>};
} else {
$lock_message = qq{<TR><TD VALIGN=TOP COLSPAN=$colspan BGCOLOR=red>}.
qq{<FONT FACE=$USER::Font SIZE=$USER::Font_Size COLOR=white>}.
qq{<B>Hinweis: </B>}.
qq{Dieses Objekt ist gesperrt, weil es sich im Ordner }.
qq{'$self->{lock_info}->{lock_dir}' befindet. }.
qq{<B>ÄNDERUNGEN WERDEN NICHT GESPEICHERT!</B> }.
qq{</FONT></TD></TR>};
$save_disable = 0;
}
}
$type_field_value = 'content';
if ( $self->{event} ne 'show_version' and 
$self->{object_type} !~ m/driver-config$/) {
$back_button .= $self->object_function ("L&ouml;schen", !$delete_disable,
qq{document.IDE_Functions.event.value='ask_for_del_object';}.
qq{document.IDE_Functions.action='$IDE::Browser_Url';}.
qq{document.IDE_Functions.submit();} );
}
else { 	 
my $version = $self->{query}->param('version');
$back_button .= $self->object_function ("L&ouml;schen", 0).
qq{<INPUT TYPE=HIDDEN NAME=version VALUE="$version">};
if ( $self->{event} eq 'show_version' ) { 
$type_field_value = 'version';
$restore = "Restore Version $version";
}
}
my $next_event = 'save';	# nächstes zu schickendes Event
my $depend_checkbox;		# Einblendung der NO-Dependency Checkbox
my $mod_size = $USER::Mod_Size || 75;	# Größe des Modification-Feldes
if ( $self->{has_depend_object_types} ) {
$depend_checkbox = '<INPUT TYPE=CHECKBOX NAME=no_depend> ohne Abhängigkeiten ';
$mod_size -= 10;
}
if ( $editor_type ne 'versions') {
my $save_button;
my $event = $self->{event};
if ( $event eq 'show_version' ) {
$save_button = 'Zur&uuml;cksichern';
} elsif ( $event ne 'show_version' and $self->{lock_info} and
not $save_disable ) {
$save_button = 'Übersetzen';
$next_event = 'preprocess';
} else {
$save_button = 'Speichern';
}
unless ( $modification_bar eq "NO_MODIFICATION_BAR" ) { 
$modification_input=
qq{<TR><TD VALIGN=TOP COLSPAN=$colspan>}.
qq{${font}Modifikation:\n}.
qq{<INPUT TYPE=TEXT NAME=object_modification VALUE="$restore" }.
qq{SIZE=$mod_size>\n}.
($save_disable?"":qq{$depend_checkbox<INPUT TYPE=BUTTON VALUE=" $save_button "\n}.
qq{ onClick = "document.IDE_Functions.submit();">}).
qq{</FONT>\n</TD></TR>};
}
}
if ( 1 or not $IDE::cvs ) {
$back_button .= $self->object_function (" Versionen ",
,($editor_type ne 'versions' and 
$object_version ne $initial_version),
qq{document.IDE_Functions.event.value=}.
qq{'versions'; document.IDE_Functions.submit()}
);
}
$back_button .= "<BR>" if not $USER::Header_Buttons;
$back_button .= $self->object_function (
" Eigenschaften ",
($editor_type ne 'property' and $self->{event} ne 'show_version'),
qq{document.IDE_Functions.event.value=}.
qq{'properties'; document.IDE_Functions.submit()}
);
$back_button .= $self->object_function (
" Editieren ",
($editor_type eq 'property' or  $editor_type eq 'versions'),
qq{document.IDE_Functions.event.value=}.
qq{'edit'; document.IDE_Functions.submit()}
);
if ($editor_type eq 'property' or  $editor_type eq 'versions') {
$type_field_value = 
($editor_type eq 'property') ? 'property' : 'versions';
}
$type_field = 
qq{<INPUT TYPE=HIDDEN NAME=editor_type VALUE="$type_field_value">};
my $hd = 'header';
my $last_access = IDE_Utils::Format_Timestamp
( $self->{$hd}->Get_Tag ('LAST_MODIFY_DATE') );
my $last_user = $self->{$hd}->Get_Tag ('LAST_MODIFY_BY');
my $desc = $self->{$hd}->Get_Tag ('DESCRIPTION');
if ( $desc ne '') {
$desc = substr( $desc, 0, $USER::Description_Cut);
$self->HTML_Text_Escape(\$desc);
$desc = "<TD VALIGN=TOP>${font}${desc}</FONT></TD>";
}
my ($download_file, $download_name);
if ( $object_type ne 'log' and $object_type ne 'cipp-img' ) {
$object =~ /\.([^\.]+)$/;
$download_file = "$1.spirit-obj";
$download_name = qq{
<A HREF="$IDE::Browser_Url/$download_file?ticket=$ticket&event=download&object=$object&object_type=$object_type">$object</A>
};
} else {
$download_name = $object;
}
print <<__HTML_CODE;
<FORM NAME=IDE_Functions METHOD=POST ACTION="$url" ENCTYPE="$enc_type">
<INPUT TYPE=HIDDEN NAME=event VALUE=$next_event>
<INPUT TYPE=HIDDEN NAME=override_lock VALUE=0>
$type_field
$self->{driver_parameter_form}
<TABLE BGCOLOR=$USER::Table_Color BORDER=1 WIDTH="100%">
<TR><TD VALIGN=TOP>
${font}Objekt:&nbsp;<B>${download_name}</B>&nbsp;&nbsp;&nbsp;
Typ:&nbsp;<B>${object_type_desc}</B>
__HTML_CODE
if ( not $IDE::cvs ) {
print qq[
<BR>
Version:&nbsp;<B>${object_version}</B>&nbsp;&nbsp;&nbsp;
Zuletzt&nbsp;geändert:&nbsp;<B>$last_access</B> von <B>$last_user</B>
</FONT>
];
}
print <<__HTML_CODE
</TD>$desc<TD ALIGN=RIGHT VALIGN=TOP>
$back_button
</TD></TR>
$modification_input
$lock_message
</TABLE>
__HTML_CODE
}
sub object_function {
my $self = shift;
my ($label, $active, $onclick) = @_;
my $font = $self->{font};
my $color = $USER::Inactive_Color;
if ( $USER::Header_Buttons ) {
if ( $active ) {
return	qq{${font}<INPUT TYPE=BUTTON VALUE=" $label " }.
qq{onClick="$onclick"></FONT>};
} else {
return	qq{<FONT FACE=$USER::Font COLOR=$color SIZE=$USER::Font_Size>}.
qq{<INPUT TYPE=BUTTON VALUE=" $label "></FONT>};
}
} else {
$label =~ s/^\s+//;
$label =~ s/\s+$//;
if ( $active ) {
return	qq{${font}<A HREF="javascript:$onclick">$label</A></FONT> };
} else {
return	qq{<FONT FACE=$USER::Font COLOR=$color SIZE=$USER::Font_Size>}.
qq{$label</A></FONT> };
} 
}
}
sub Print_Editor_Footer {
print "</FORM>";
}
sub Print_Property_Header {
my $self = shift;
my $edit_button_text = shift;
$self->Print_Editor_Header( "property", undef, undef, $edit_button_text) 
if $self->{event} ne 'show_version';
my $font = $self->{font};
my $url = $self->{url};
my $description = $self->{header}->Get_Tag ("DESCRIPTION");
my $copyright = $self->{header}->Get_Tag ("COPYRIGHT");
print <<__HTML_CODE;
<P><B>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Eigenschaften</FONT></B><P>
<TABLE BGCOLOR=$USER::Table_Color BORDER=1>
<TR><TD VALIGN=TOP>
<TABLE>
<TR><TD VALIGN=TOP>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Beschreibung:
</FONT>
</TD><TD VALIGN=TOP>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<TEXTAREA NAME=prop_description ROWS=4 COLS=40
WRAP=virtual>$description</TEXTAREA>
</FONT>
</TD></TR>
<TR><TD VALIGN=TOP>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Copyright:
</FONT>
</TD><TD VALIGN=TOP>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<TEXTAREA NAME=prop_copyright ROWS=2 COLS=40
WRAP=virtual>$copyright</TEXTAREA>
</FONT>
</TD></TR>
</TABLE>
</TD></TR>
</TABLE>
__HTML_CODE
}
sub Print_Property_Footer {
my $self = shift;
if  ($self->{event} ne 'show_version' ) {
print "</FORM>";
}
}
sub Version_Management {
my $self = shift;
my $edit_button_text = shift;
my $version_event = $self->{query}->param('version_event');
$version_event ||= '';
if ( $version_event eq '1' or $version_event eq '2' ) {
$self->Set_Release();
}
$self->Delete_Versions() if $version_event eq 'del';
$self->Save_Version_Number() if $version_event eq 'change';
$self->Print_HTTP_Header();
$self->Print_HTML_Header();
$self->Print_Versions_Header( $edit_button_text);
$self->Print_Versions_Footer();
$self->Print_HTML_Footer();	
}
sub Set_Release {
my $self = shift;
my $increment = $self->{query}->param('version_event');
my $object_version = $self->{header}->Get_Tag ("OBJECT_VERSION");
my $new_object_version = $object_version;
if ( $increment == 1 ) {
$new_object_version =~ s/^([^\.]+)//;
my $release = $1;
my $tmp_initial_version = $initial_version;
$tmp_initial_version =~ s/^[^\.]+//;
$new_object_version = ( ++$release . $tmp_initial_version);
} 
else {
$new_object_version =~ s/^([^\.]+\.)([^\.]+)//;
$new_object_version = $1;
my $release = $2;
my $tmp_initial_version = $initial_version;
$tmp_initial_version =~ s/^[^\.]+\.[^\.]+//;
$new_object_version .= ( ++$release . $tmp_initial_version);
}
$self->{header} = undef;
my $read_fh = $self->{filehandle};
close $read_fh;
open (IDE_OBJECT_READ, "+<$self->{object_path}");
my $header = new IDE_Header ( *IDE_OBJECT_READ, $self->{driver_tags});
if ( $IDE_Header::init_status != 1 ) {
Print_Error_Message("Die Objektdatei ist fehlerhaft: ".
"$IDE_Header::init_status!");
}
my $modification_date = IDE_Utils::Get_Timestamp();
my $modification_history = $header->Get_Tag("MODIFICATION_HISTORY");
my $description = $self->{query}->param('description');
$Text::Wrap::columns -= $IDE_Header::spaces;
eval { $description = wrap ( '', '', $description); };
if ( $modification_history =~ 
s/\n\n$object_version[^\n]+\n([\s\S]+)/\n\n$new_object_version $modification_date $self->{username}/ and $description ne '') {
$modification_history .= "\n$description";    
}
elsif ( $description ne '') {
$modification_history .= "\n\n$new_object_version $modification_date ".
"$self->{username}\n$description";    
}
$header->Put_Tag ("OBJECT_VERSION", $new_object_version);
$header->Put_Tag ("MODIFICATION_HISTORY", $modification_history);
$header->Put_Tag ("LAST_MODIFY_BY", $self->{username});
$header->Put_Tag ("LAST_MODIFY_DATE", $modification_date);
my $content;
while (<IDE_OBJECT_READ>) {
$content .= $_;
}
seek IDE_OBJECT_READ, 0,0;
truncate IDE_OBJECT_READ, 0;
my $error = $header->Write_IDE_Header ( *IDE_OBJECT_READ );
print IDE_OBJECT_READ $content;
close IDE_OBJECT_READ;
$self->{header} = $header;
}
sub Version_Restore {
my $self = shift;
my $object_version = $self->{query}->param('version');
$self->Prepare_Save ();
my $new_object_version = $self->{header}->Get_Tag ("OBJECT_VERSION");
my $input_fh = new FileHandle;
my $output_fh = new FileHandle;
my $version_dir;
($version_dir = $self->{object_path}) =~ s!([^/]+)$!.$1!;
my $object_name = $1;
$input_fh->open("<$version_dir/$object_name-$object_version");
$output_fh->open(">$self->{object_path}");
my $header = new IDE_Header ( $input_fh);
if ( $IDE_Header::init_status != 1 ) {
Print_Error_Message("Die Objektdatei $object_version ist fehlerhaft: ".
"$IDE_Header::init_status!");
}
my $description = $header->Get_Tag('DESCRIPTION');
my $copyright = $header->Get_Tag('COPYRIGHT');
$self->{header}->Put_Tag ("DESCRIPTION", $description);
$self->{header}->Put_Tag ("COPYRIGHT", $copyright);
my ( $tag, @user_tag_list);
@user_tag_list = split ( /\s/, $self->{driver_tags});
foreach $tag ( @user_tag_list) {
$self->{header}->Put_Tag ( $tag, $header->Get_Tag($tag));    
}
my $error = $self->{header}->Write_IDE_Header ( $output_fh);
my ( $line, $content);
while ( defined( $line = <$input_fh>) ) {
print $output_fh $line;
$content .= $line
}
$output_fh->close;
$input_fh->close;
return \$content;
}
sub Open_Old_Version {
my $self = shift;
my $object_version = $self->{query}->param('version');
my $read_fh = $self->{filehandle};
close $read_fh;
my $version_dir;
($version_dir = $self->{object_path}) =~ s!([^/]+)$!.$1!;	
my $object_name = $1;
$self->{object_path} = "$version_dir/$object_name-$object_version";
open (IDE_OBJECT_READ, $self->{object_path});
my $header = new IDE_Header ( *IDE_OBJECT_READ );
if ( $IDE_Header::init_status != 1 ) {
Print_Error_Message("Die Objektdatei ist fehlerhaft: ".
"$IDE_Header::init_status!");
}
$self->{header} = $header;
$self->{filehandle} = *IDE_OBJECT_READ;
}
sub Print_Versions_Header {
my $self = shift;
my $edit_button_text = shift;
my $select_width = '150';
my $empty_string = ' - ';
my $url = $self->{url};
my $ticket = $self->{ticket};	
my $object = $self->{object};
my $object_type = $self->{object_type};
my $project = $self->{project};
my $version = $self->{query}->param('version');
my $version_hash_ref = $self->Get_desc_Versions();
my $version_list_ref = $self->Get_all_Versions( $version_hash_ref);
my $last_version = pop @$version_list_ref;
$self->Print_Editor_Header("versions", undef, undef, $edit_button_text);
my ($version_table, $select_options);
foreach $version ( @$version_list_ref) {
my $description = $version_hash_ref->{$version}{description} || $empty_string;
my $username = $version_hash_ref->{$version}{username} || $empty_string;
my $date = $version_hash_ref->{$version}{date} || $empty_string;
$date = IDE_Utils::Format_Timestamp	( $date);
$version_table .= 
qq{<TR><TD>\n<FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{<A HREF="$url?event=show_version&ticket=$ticket&project=$project}.
qq{&object=$object&object_type=$object_type&version=$version}.
qq{&editor_type=content">$version</A>}.
qq{</FONT>\n</TD>\n}.
qq{<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{$date\n</FONT></TD>\n}.
qq{<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{$username\n</FONT></TD>\n}.
qq{<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{$description\n</FONT></TD></TR>\n};
$select_options .= 
qq{<option value="$version"><b>$version</b>\n};
}
$version = $last_version;
my $description = $version_hash_ref->{$version}{description} || $empty_string;
my $username = $version_hash_ref->{$version}{username} || $empty_string;
my $date = $version_hash_ref->{$version}{date} || $empty_string;
$date = IDE_Utils::Format_Timestamp( $date);
$version_table .= 
qq{<TR><TD>\n<FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{$version}.
qq{</FONT>\n</TD>\n}.
qq{<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{$date\n</FONT></TD>\n}.
qq{<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{$username\n</FONT></TD>\n}.
qq{<TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>}.
qq{$description\n</FONT></TD></TR>\n};
$description = '' if $description eq $empty_string;
$description =~ s/\n/ /g;
print <<__HTML_CODE;
<P><B>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Versionsverwaltung</FONT></B><P>
<TABLE BGCOLOR=$USER::Table_Color BORDER=1>
<TR><TD><BR>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Versionstabelle:</FONT><BR>
<TABLE BORDER=1 WIDTH="90%" ALIGN=CENTER>
<TH><FONT FACE=$USER::Font SIZE=$USER::Font_Size>Version</FONT>
</TH><TH><FONT FACE=$USER::Font SIZE=$USER::Font_Size>Datum</FONT>
</TH><TH><FONT FACE=$USER::Font SIZE=$USER::Font_Size>Name</FONT>
</TH><TH><FONT FACE=$USER::Font SIZE=$USER::Font_Size>Beschreibung</FONT>
</TH></TR>$version_table
</TABLE> <P>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Beschreibung:
<INPUT TYPE=HIDDEN NAME="version_event">
<INPUT TYPE=TEXT NAME="description" VALUE="$description" SIZE=80>
<DIV ALIGN=RIGHT> aktuelle Version:
<INPUT TYPE=BUTTON VALUE=" erste Nummer inkrementieren "
onClick = "document.IDE_Functions.event.value='versions';
document.IDE_Functions.version_event.value='1';
document.IDE_Functions.submit();">
<INPUT TYPE=BUTTON VALUE=" zweite Nummer inkrementieren "
onClick = "document.IDE_Functions.event.value='versions';
document.IDE_Functions.version_event.value='2';
document.IDE_Functions.submit();">
</DIV> </FONT></TD></TR>
</TABLE><BR>
<TABLE BGCOLOR=$USER::Table_Color BORDER=1>
<TR><TD>
<TABLE WIDTH="100%">
<TR><TD VALIGN=TOP><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Versionen l&ouml;schen:</FONT>
</TD><TD ALIGN=RIGHT><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<SELECT NAME="delete_versions" MULTIPLE SIZE=5 WIDTH=$select_width>
$select_options</SELECT></FONT> </TD></TR>
<TR><TD COLSPAN=2 ALIGN=RIGHT>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<INPUT TYPE=BUTTON VALUE=" L&ouml;schen "
onClick = "document.IDE_Functions.event.value='versions';
document.IDE_Functions.version_event.value='del';
document.IDE_Functions.submit();"></FONT>
</TD></TR>
</TABLE>
</TD></TR><TR><TD><TABLE WIDTH="100%"><TR><TD COLSPAN=2>
<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
Anzahl der Versionen, die im System gespeichert werden sollen
</FONT></TD></TR><TR><TD><FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<INPUT TYPE=TEXT NAME="versionsnumber" VALUE="$USER::Versions_Number" 
SIZE=3></FONT></TD>
<TD ALIGN=RIGHT> <FONT FACE=$USER::Font SIZE=$USER::Font_Size>
<INPUT TYPE=BUTTON VALUE=" Anzahl speichern "
onClick = "document.IDE_Functions.event.value='versions';
document.IDE_Functions.version_event.value='change';
document.IDE_Functions.submit();"></FONT>
</TD></TR></TABLE>
</FONT></TD></TR>
</TABLE>
__HTML_CODE
}
sub Print_Version_Message {
my $self = shift;
my $font = $self->{font};
my $object_version = $self->{query}->param('version');
print <<__HTML_CODE;
<P>$font
<B>Ansicht der Version $object_version</B>
(vorgenommene &Auml;nderungen werden <BLINK>nicht</BLINK> gespeichert)</FONT><P>
__HTML_CODE
}
sub version_sort {
my @a_list = split ( '\.', $a);    
my @b_list = split ( '\.', $b);    
$a_list[0] <=>  $b_list[0]
or
$a_list[1] <=>  $b_list[1]
or
$a_list[2] <=>  $b_list[2]
or
$a_list[3] <=>  $b_list[3];
}
sub Get_all_Versions {
my $self = shift;
my $version_hash_ref = shift;
my $dh = new FileHandle;
my $fh = new FileHandle;
my $version_dir;
($version_dir = $self->{object_path}) =~ s!([^/]+)$!.$1!;	
my $object_name = $1;
opendir $dh, $version_dir or 
Print_Error_Message
("Verzeichnis $version_dir konnte nicht geoeffnet werden");
my @version_list = grep !/^\./, readdir $dh;
closedir $dh;
my $version;
foreach $version ( @version_list) {
my $filename = $version;
$version =~ s/^${object_name}-//;     
unless ( defined $version_hash_ref->{$version} ) {
$fh->open("<$version_dir/$filename");
my $header = new IDE_Header ( $fh );
$fh->close;
if ( $IDE_Header::init_status != 1 ) {
Print_Error_Message("Die Objektdatei $version ist fehlerhaft: ".
"$IDE_Header::init_status!");
}
$version_hash_ref->{$version}{username} = 
$header->Get_Tag ("LAST_MODIFY_BY");
$version_hash_ref->{$version}{date} = 
$header->Get_Tag ("LAST_MODIFY_DATE");
}
}
$version = $self->{header}->Get_Tag ("OBJECT_VERSION");
push @version_list,	$version;
unless ( defined $version_hash_ref->{$version} ) { 
$version_hash_ref->{$version}{username} = 
$self->{header}->Get_Tag ("LAST_MODIFY_BY");
$version_hash_ref->{$version}{date} = 
$self->{header}->Get_Tag ("LAST_MODIFY_DATE");	
}
@version_list = sort version_sort @version_list;
if ( $USER::Versions_Number ne '') {
my $number = scalar(@version_list) - $USER::Versions_Number;
if ( $number > 0) {
foreach (1..$number) {
$version = shift @version_list;
unlink "$version_dir/$object_name-$version";
}
}
}
shift @version_list if $version_list[0] eq $initial_version;
return \@version_list;
}
sub Get_desc_Versions {
my $self = shift;
my $modification_history =
$self->{header}->Get_Tag ("MODIFICATION_HISTORY");
my @modification_list = split ( "\n\n", $modification_history);
my %version_hash;
my $element;
foreach $element ( @modification_list) {
my ( $version, $date, $username, $description) = split(/\s+/, $element, 4);
$version_hash{$version}{date} = $date;
$version_hash{$version}{username} = $username;
$version_hash{$version}{description} = $description
}
return \%version_hash;
}
sub Delete_Versions {
my $self = shift;
my @version_list = $self->{query}->param('delete_versions');
my $version_dir;
($version_dir = $self->{object_path}) =~ s!([^/]+)$!.$1!;	
my $object_name = $1;
my $version;
foreach $version ( @version_list) {
unlink "$version_dir/$object_name-$version";
}
}
sub Save_Version_Number {
my $self = shift;
my $versions_number = $self->{query}->param('versionsnumber');
$versions_number =~ s/\s//g;
$versions_number = '' if $versions_number =~ m/[^0-9]/ or $versions_number == 0;
my $config_obj = new Configure( $IDE::Config_File, $self->{username});
$config_obj->Write( $self->{username}, 'Versions_Number', $versions_number);
$USER::Versions_Number = $versions_number;
}
sub Print_Versions_Footer {
print "</FORM>\n";
}
sub Get_Depend_Object {
my $self = shift;
my ($class) = @_;
$class = $self->{driver}."_".$class;
my $depend_dir = $self->{project_dir}."/src";
my $project = $self->{project};
my $Depend = new Depend ($project, $class, $depend_dir);
if ( ! $Depend->{init_status} ) {
die "Konnte Depend ('$class', '$depend_dir') ".
"nicht initialisieren: ".$Depend->{init_status};
}
return $Depend;
}
sub Get_Object_Path {
my $self = shift;
my ($object, $object_type) = @_;
$object =~ /^([^\.]+)/;
my $project = $1;
my $project_dir = $self->{project_src_hash}->{$project};
my $object_path = $object;
$object_path =~ s/^$project\.//;
$object_path =~ s!\.!/!g;
$object_path = "$project_dir/$object_path.$object_type";
return $object_path;
}
sub Get_IDE_Header {
my $self = shift;
my ($object, $object_type) = @_;
my $object_path = $self->Get_Object_Path ($object, $object_type);
open (IDE_HEADER_READ, $object_path) or
return undef;
my $IDE_Header = new IDE_Header
(\*IDE_HEADER_READ, $self->{driver_tags});
my ($key, $val);
my %header_hash;
while ( ($key, $val) = each %{$IDE_Header->{header_hash}} ) {
$val =~ s/^\s*//;
$val =~ s/\s*$//;
$header_hash{$key} = $val;
}
$header_hash{IDE_OBJECT_CONTENT} = join '', <IDE_HEADER_READ>;
close IDE_HEADER_READ;
return \%header_hash;
}
sub Get_Driver_Tags {
my $self = shift;
my (%hash, $tag, $value);
foreach $tag (split ("\t", $self->{driver_tags})) {
$value = $self->{header}->Get_Tag($tag);
$value = '' if $value eq $IDE_Header::UNKNOWN_KEY;
$hash{$tag} = $value;
}
return \%hash;
}
sub Put_Driver_Tags {
my $self = shift;
my ($href) = @_;
my $value;
my ($tag);
foreach $tag (split ("\t", $self->{driver_tags})) {
if ( $value = $href->{$tag} ) {
$self->{header}->Put_Tag($tag, $value);
} else {
$self->{header}->Put_Tag($tag, "");
}
}
}
sub Print_HTTP_Header {
print "Content-type: text/html\n\n";
}
sub Print_HTML_Header {
my $self = shift;
my ($onload, $title) = @_;
$onload ||= '';
$title  ||= 'spirit';
if ( $onload ne '' ) {
$onload = qq{onLoad="$onload"};
}
print <<__HTML_CODE;
<HTML>
<HEAD>
<TITLE>$title</TITLE>
<style type="text/css">A:visited,A:link,A:active{text-decoration:none}</style>
</HEAD>
<BODY BGCOLOR=$USER::BG_Color TEXT="$USER::Text_Color"
ALINK="$USER::Link_Color" VLINK="$USER::Link_Color"
LINK="$USER::Link_Color" $onload>
__HTML_CODE
}
sub Print_HTML_Footer {
print "</BODY></HTML>\n";
}
sub Print_Error_Message {
my $error_string = shift;
print "Content-type: text/plain\n\n";
print "$error_string\n";
exit;    
}
sub Get_Objects_In_Folder {
my $self = shift;
my ($folder, $object_type) = @_;
my $Project = new Project ($IDE::Project_File, $IDE::Driver_File);
my $href = $Project->Get_Objects_In_Folder ($folder, $object_type);
return $href->{$self->{driver}};
}
1;
