package CIPP::Runtime;
$REVISION = q$Revision: 1.1.1.1 $;
$VERSION = "0.32";
use FileHandle;
use Cwd;
use Carp;
sub Read_Config {
my ($filename, $nocache) = @_;
$nocache = 1;
die "CONFIG\tDatei '$filename' nicht gefunden" if not -f $filename;
my $file_timestamp = (stat($filename))[9];
if ( $nocache or not defined $CIPP::Runtime::cfg_timestamp{$filename} or
$CIPP::Runtime::cfg_timestamp{$filename} < $file_timestamp ) {
my $fh = new FileHandle;
open ($fh, $filename);
eval join ('', <$fh>)."\n1;";
die "CONFIG\t$@" if $@;
close $fh;
$CIPP::Runtime::cfg_timestamp{$filename} = $file_timestamp;
}
}
sub Exception {
my ($die_message) = @_;
my (@type) = split ("\t", $die_message);
my $message = pop @type;
if ( (scalar @type) == 0 ) {
push @type, "general";
}
my $type = join ("::", @type);
my $log_error = Log ("EXC", "TYPE=$type, MESSAGE=$message");
if ( $log_error ) {
$message .= "<P><BR><B>Diese Exception konnte nicht im Logfile vermerkt werden!</B><BR>\n";
$message .= "=> $log_error";
}
print "Content-type: text/html\n\n" if ! $CIPP_Exec::cipp_http_header_printed;
print "<P>$CIPP_Exec::cipp_error_text<P>";
if ( $CIPP_Exec::cipp_error_show ) {
print "<P><B>EXCEPTION: </B>$type<BR>\n",
"<B>MESSAGE: </B>$message<P>\n";
if ( $message =~ /compilation errors/ ) {
print "<P>Die Compiler-Fehlermeldung finden Sie im Logfile des\n";
print "Webservers.<P>\n";
}
}
eval {
confess "STACK-BACKTRACE";
};
print "<p><pre>$@</pre>\n";
}
sub Log {
my ($type, $message, $filename, $throw) = @_;
my $time = scalar (localtime);
$message =~ s/\s+$//;
my $program;
if ( not $CIPP_Exec::apache_mod ) {
$program = $0;
$program =~ s!$CIPP_Exec::cipp_cgi_dir/!!;
$program =~ s!/!.!g;
$program =~ s!\.cgi$!!;
} else {
$program = $CIPP_Exec::apache_program;
}
my $msg = "$main::ENV{REMOTE_ADDR}\t$program\t$type\t$message";
my $log_error;
if ( not $CIPP_Exec::apache_mod ) {
if ( $filename ne '' ) {
if ( $filename !~ m!^/! ) {
my $dir = $CIPP_Exec::cipp_log_file;
$dir =~ s!/[^/]+$!!;
$filename = "$dir/$filename";
}
} else {
$filename = $CIPP_Exec::cipp_log_file;
}
if ( open (cipp_LOG_FILE, ">> $filename") ) {
if ( ! print cipp_LOG_FILE "$time\t$msg\n" ) {
$log_error = "Konnte nicht in $filename schreiben";
}
close cipp_LOG_FILE;
} else {
$log_error = "Konnte $filename nicht zum Schreiben öffnen";
}
} else {
$CIPP_Exec::apache_request->log_error ("Log: $msg");
}
return $log_error;
}
sub HTML_Quote {
my ($text) = @_;
$text =~ s/&/&amp;/g;
$text =~ s/</&lt;/g;
$text =~ s/\"/&quot;/g;
return $text;
}
sub Field_Quote {
my ($text) = @_;
$text =~ s/&/&amp;/g;
$text =~ s/\"/&quot;/g;
return $text;
}
sub URL_Encode {
my ($text) = @_;
$text =~ s/(\W)/(ord($1)>15)?(sprintf("%%%x",ord($1))):("%0".sprintf("%lx",ord($1)))/eg;
return $text;
}
sub Execute {
my ($name, $output, $throw) = @_;
$throw ||= 'EXECUTE';
$name =~ s!\.!/!g;
my $dir=$name;
$dir =~ s!/[^/]+$!!;
$dir = $CIPP_Exec::cipp_cgi_dir."/$dir";
$script = $CIPP_Exec::cipp_cgi_dir."/$name.cgi";
my $cwd_dir = cwd();
chdir $dir
or die "$throw\tKonnte nicht nach Verzeichnis $dir wechseln";
my $cgi_fh = new FileHandle;
if ( ! open ($cgi_fh, $script) ) {
chdir $cwd_dir;
die "$throw\tKonnte '$script' nicht öffnen";
}
my $cgi_script = join ("", <$cgi_fh>);
close $cgi_fh;
my $save_fh = "save".(++$CIPP::Runtime::save_stdout);
if ( ! open ($save_fh, ">&STDOUT") ) {
chdir $cwd_dir;
die "$throw\tKonnte STDOUT nicht duplizieren";
}
my $catch_file;
if ( ref ($output) eq 'SCALAR' ) {
do {
my $r = int(rand(424242));
$catch_file = "/tmp/execute".$$.$r;
} while ( -e $catch_file );
} else {
$catch_file = $output;
}
close STDOUT;
if ( ! open (STDOUT, "> $catch_file") ) {
open (STDOUT, ">&$save_fh")
or die "$throw\tKonnte STDOUT nicht restaurieren";
close $save_fh;
chdir $cwd_dir;
die "$throw\tKonnte '$catch_file' nicht zum Schreiben öffnen";
}
$CIPP_Exec::_cipp_in_execute = 1;
$CIPP_Exec::_cipp_no_http = 1;
eval $cgi_script;
my $error = $@;
$CIPP_Exec::_cipp_no_http = undef;
$CIPP_Exec::_cipp_in_execute = undef;
chdir $cwd_dir;
close STDOUT;
open (STDOUT, ">&$save_fh")
or die "$throw\tKonnte STDOUT nicht restaurieren";
close $save_fh;
if ( ref ($output) eq 'SCALAR' ) {
my $catch_fh = new FileHandle;
open ($catch_fh, $catch_file)
or die "$throw\tFehler beim Einlesen der Scriptausgabe";
$$output = join ("", <$catch_fh>);
close $catch_fh;
unlink $catch_file
or die "$throw\tFehler beim Löschen der Datei '$catch_file'";
}
if ( $error ne '' ) {
if ( ref ($output) ne 'SCALAR' ) {
unlink $catch_file;
}
die "$throw\t$error" if $error ne '';
}
return 1;
}
sub Get_Object_URL {
my ($object, $throw) = @_;
$throw ||= "geturl";
my $object_name = $object;
$object =~ s/\./\//g;	# Punkte durch Slashes ersetzen
$object =~ s![^\/]*!$CIPP_Exec::cipp_project!;	
if ( -f "$CIPP_Exec::cipp_cgi_dir/$object.cgi" ) {
return "$CIPP_Exec::cipp_cgi_url/$object.cgi";
}
my @filenames = <$CIPP_Exec::cipp_doc_dir/$object.*>;
if ( scalar @filenames == 0 ) {
die "$throw\tKonnte Objekt '$object_name' nicht auflösen";
} elsif ( scalar @filenames > 1 ) {
die "$throw\tObject-Name '$object_name' ist nicht eindeutig";
}
my $file = $filenames[0];
$file =~ s/^$CIPP_Exec::cipp_doc_dir\///;
return "$CIPP_Exec::cipp_doc_url/$file";
}
1;
__END__
=head1 NAME
CIPP::Runtime - Runtime library for CIPP generated perl programs
=head1 DESCRIPTION
This module is used by Perl programs which are generated by CIPP.
=head1 AUTHOR
Jörn Reder, joern@dimedis.de
=head1 COPYRIGHT
Copyright 1997-1999 dimedis GmbH, All Rights Reserved
This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself.
=head1 SEE ALSO
perl(1), CIPP (3pm)
