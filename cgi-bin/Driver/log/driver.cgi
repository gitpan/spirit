#!/usr/bin/perl
BEGIN { 
$0 =~ m!^(.*)[/\\][^/\\]+$!;    # Windows NT Netscape Workaround
chdir $1;
require "../../../etc/ide.cnf";
unshift ( @INC, $IDE::Lib);
}
use Driver;	# spirit Driver Klasse fuer die ganze laestige Arbeit
use strict;
my $TRUE = 1;
my $FALSE = 0;
my $edit_button_text = "Ansicht";
my $CANT_READ = -1;
my $NO_TEXT_FILE = -2;
my $Driver = new Driver ("log");	
my $object_type = $Driver->{object_type};
my $event = $Driver->{event};
if ( $event eq 'new_object' ) {			# Objekt wurde gerade erzeugt
New_Object ($Driver);
} elsif ($event eq 'edit' ) {			# Editor-Seite aufbauen
Editor ($Driver);
} elsif ( $event eq 'save' ) {			# Objekt speichern
Save ($Driver);
} elsif ( $event eq 'properties' ) {		# Properties editieren
Property_Editor ($Driver);
} elsif ( $event eq 'versions' ) {		# Versionskontrolle
Version_Management ($Driver);
} elsif ( $event eq 'show_version' ) {		# Version anzeigen
Version_Show ($Driver);
} elsif ( $event eq 'ask_for_delete' ) {	# Loesch-Nachfrage
Ask_For_Delete ($Driver);
} elsif ( $event eq 'delete' ) {		# Objekt loeschen
Delete ($Driver);
}
exit;
sub New_Object {
my ($Driver) = @_;
my $object_type = $Driver->{object_type};
if ( $object_type eq 'log' ) {
Property_Editor ($Driver);
} else {
Editor ($Driver);
}
}
sub Editor {
my ($Driver) = @_;
my $object_type = $Driver->{object_type};
Text_Editor ($Driver);
}
sub Save {
my ($Driver) = @_;
my $object_type = $Driver->{object_type};
my $editor_type = $Driver->{query}->param('editor_type');
my $status;
if ( $editor_type eq 'property' ) {
$status = Property_Save ($Driver);
} elsif ( $editor_type eq 'version' ) {
Version_Restore ($Driver);
} elsif ( $editor_type eq 'content' ) {
Text_Save ($Driver);
}
if ( $object_type eq 'log') {
if ( $editor_type eq 'property' and $status != $TRUE ) {
Property_Editor  ($Driver, $status);
}
else {
Text_Editor ($Driver);
}
}
}
sub Ask_For_Delete {
my ($Driver) = @_;
}
sub Delete {
my ($Driver) = @_;
}
sub Property_Editor {
my ($Driver,
$status) = @_;
if ( $Driver->{event} ne 'show_version' ) {
$Driver->Print_HTTP_Header();
$Driver->Print_HTML_Header();
}
$Driver->Print_Property_Header($edit_button_text);
if ( $Driver->{object_type} eq "log" ) {
my $logfilepath = $Driver->{header}->Get_Tag("LOGFILE_PATH");
my $linenumber = $Driver->{header}->Get_Tag("LINE_NUMBER");
LOG_Properties ($Driver, $logfilepath, $linenumber, $status);
}
if ( $Driver->{event} ne 'show_version' ) {
$Driver->Print_Property_Footer();
$Driver->Print_HTML_Footer();	
}
}
sub Property_Save {
my ($Driver) = @_;
my $driver_tags = $Driver->Get_Driver_Tags();
if ( $Driver->{object_type} eq 'log' ) {
my $logfile_path = $Driver->{query}->param('logfilepath');
return $CANT_READ unless -r $logfile_path;
return $NO_TEXT_FILE unless -f $logfile_path && -T _;
$driver_tags->{LOGFILE_PATH} = $logfile_path;	
my $linenumber = $Driver->{query}->param('linenumber');
$linenumber =~ s/\D//g;
$linenumber ||= 20;
$driver_tags->{LINE_NUMBER} = $linenumber;
}
my $object_fh = $Driver->{filehandle};
$Driver->Prepare_Save();
$Driver->Put_Driver_Tags ($driver_tags);
my $object_path = $Driver->{object_path};
open (LOG_OBJECT_SAVE, "> $object_path") or
die "SAVE: > $object_path";
$Driver->{header}->Write_IDE_Header ( *LOG_OBJECT_SAVE );
close LOG_OBJECT_SAVE;
return $TRUE;
}
sub Version_Management {
my ($Driver) = @_;
$Driver->Version_Management($edit_button_text);
}
sub Version_Show {
my ($Driver) = @_;
$Driver->Open_Old_Version();
$Driver->Print_HTTP_Header();
$Driver->Print_HTML_Header();
$Driver->Print_Editor_Header( undef, undef, undef, $edit_button_text);
$Driver->Print_Version_Message();
Property_Editor ($Driver);
$Driver->Print_Editor_Footer();
$Driver->Print_HTML_Footer();
}
sub Version_Restore {
my ($Driver) = @_;
my $object_type = $Driver->{object_type};
$Driver->Version_Restore ();
}
sub Text_Editor {
my ($Driver) = @_;
my $content_ref;
my $input_size = 10;
my $logfilename = $Driver->{header}->Get_Tag("LOGFILE_PATH");
my $linenumber = $Driver->{header}->Get_Tag("LINE_NUMBER"); 
my $content_buffer = '';
my $line_count;
open TAIL, "<$logfilename";# or die "Kein Zugriff auf $logfilename: $!\n";
while (<TAIL>) {
$content_buffer .= $_;
$line_count++;
if ( $line_count > $linenumber) {
$content_buffer =~ s/.*\n//;
$line_count--;
}
}
close TAIL;
$content_ref = \$content_buffer;
$Driver->HTML_Text_Escape ($content_ref);
if ( $Driver->{event} ne 'show_version' ) {
$Driver->Print_HTTP_Header();
$Driver->Print_HTML_Header();
$Driver->Print_Editor_Header( undef, undef, 
"NO_MODIFICATION_BAR", $edit_button_text);
}
my $font = $Driver->{font};
my $foo = $USER::Textarea_Cols < $USER::Textarea_Rows;	# sonst Warning
print <<__HTML_CODE;
<P>$font
<B>Ausgabe des Logfiles:</B> $logfilename</FONT>
<TABLE BGCOLOR=$USER::Table_Color BORDER=1 WIDTH="100%">
<TR><TD><TABLE WIDTH="100%"><TR><TD ALIGN=LEFT>
${font}Anzahl der Zeilennummern:
<INPUT TYPE=TEXT NAME="linenumber" VALUE="$linenumber" 
SIZE="$input_size"></FONT>
</TD><TD ALIGN=RIGHT>
$font<INPUT TYPE=BUTTON NAME="updatelog" VALUE="Ausgabe erneuern"
onClick = "document.IDE_Functions.event.value='save';
document.IDE_Functions.submit();"></FONT>
</TD></TR></TABLE></TD></TR></TABLE>
</FORM><FORM>
<TEXTAREA NAME=source COLS=$USER::Textarea_Cols ROWS=$USER::Textarea_Rows
WRAP=VIRTUAL>$$content_ref</TEXTAREA>
<BR>
__HTML_CODE
if ( $Driver->{event} ne 'show_version' ) {
$Driver->Print_Editor_Footer();
$Driver->Print_HTML_Footer();
}
}
sub Text_Save {
my ($Driver) = @_;
my $driver_tags = $Driver->Get_Driver_Tags();
$Driver->Prepare_Save ();
my $linenumber = $Driver->{query}->param('linenumber');
$linenumber =~ s/\D//g;
$linenumber ||= 20;
$driver_tags->{LINE_NUMBER} = $linenumber;
$Driver->Put_Driver_Tags ($driver_tags);
my $object_path = $Driver->{object_path};
open (LOG_TEXT_SAVE, "> $object_path") or
die "SAVE: > $object_path";
my $error = $Driver->{header}->Write_IDE_Header ( *LOG_TEXT_SAVE );
close LOG_TEXT_SAVE;
}
sub LOG_Properties {
my ($Driver, $logfilepath, $linenumber, $status) = @_;
my $message = "";
$status ||= 1;
$message = "Kein Leserecht auf dieser Datei" if $status == $CANT_READ;
$message = "Sie haben keine Textdatei angegeben" if $status == $NO_TEXT_FILE;
if ( $status == 1 ) {
$logfilepath ||= "";
$linenumber ||= "50";
} 
else {
$logfilepath = $Driver->{query}->param('logfilepath');
$linenumber = $Driver->{query}->param('linenumber');
}
my $size_num = 10;
my $size_str = 50;
my $font = $Driver->{font};
my $error_font = $Driver->{error_font};
print <<__HTML_CODE;
<P>
<TABLE BGCOLOR=$USER::Table_Color BORDER=1>
<TR><TD>
<TABLE>
<TR><TD>
$font
Verzeichnispfad des Logfiles:
</FONT>
</TD><TD>
$font
<INPUT TYPE=TEXT NAME="logfilepath" VALUE="$logfilepath" SIZE="$size_str">
</FONT>
</TD></TR>
<TR><TD>
$font
Anzahl der sichtbaren Zeilen:
</FONT>
</TD><TD>
$font
<INPUT TYPE=TEXT NAME="linenumber" VALUE="$linenumber" SIZE="$size_num">
</FONT>
</TD></TR>
</TABLE>
</TD></TR>
</TABLE>
<P>$error_font
$message</FONT>
__HTML_CODE
}
