#!/usr/local/bin/perl -w
package Header;
use strict;
require "flush.pl";
$Header::FILEHANDLE_MISSING = -1;    # Dateizeiger ist nicht gueltig
$Header::UNKNOWN_KEY = -2;           # Schluesselwort ist nicht bekannt
$Header::NOT_INITIALIZED = -3;       # Instanz konnte nicht erzeugt werden
$Header::LOCK_ERROR = -4;            # Fehler beim Sperren der Datei
my $LOCK_SH = 1;                # Sperren einer Datei zum gemeinsamen Lesen
my $LOCK_EX = 2;                # exklusives Sperren einer Datei
my $LOCK_UN = 8;                # loesen der Sperre
my $TRUE = 1;
my $FALSE = 0;
$Header::version = "0.4.0";          # derzeitige Version der Klasse Header
$Header::init_status =
$TRUE ;       # Status, ob eine Instanz erzeugt werden konnte
sub new {
my $type = shift;        # Objekttyp
my ($file,               # Dateihandle
$delimiter) = @_;    # Begrenzer fuer den Header
my $self = {};	     # Instanz-Hash fuer Instanzvariablen
my ($line,               # eingelesene Zeile
$key);               # Schluessel aus dem Header
return undef if $Header::init_status ==
$FALSE;
$self->{delimiter} = $delimiter;
if ( defined($file)) {
my $f;
if ( $f = flock($file, $LOCK_SH) ) {	    
while ( defined($line = <$file>)) {
last if $line =~ m/^\#\s*$delimiter/; 
}	
my $in_key = $FALSE;
$delimiter .= '_END';
while ( defined($line = <$file>) 
and !( $line =~ m/^\#\s*$delimiter/ ) ) {	
$line =~ s/^\#//;    
if ( $in_key == $FALSE) {
if ( $line =~ s/^\s*\$(.*?)://) {
$key = $1;
$self->{header_hash}{$key} = $line;
$in_key = $TRUE 
unless $self->{header_hash}{$key} =~ s/ \$\r?\n$//;
}
} else {
$self->{header_hash}{$key} .= $line;
$in_key = $FALSE 
if $self->{header_hash}{$key} =~ s/ \$\r?\n$//;
}	
}	
$Header::init_status =
$FALSE unless defined($line);
} 
else {
$Header::init_status =
$FALSE;
}
}
return bless $self, $type;
}
sub Get_Tag {
my $self = shift;            # Objekttyp
my ($key) = @_;              # Uebergabeparameter	
return $Header::NOT_INITIALIZED
if $Header::init_status ==
$FALSE;
if ( defined $self->{header_hash}{$key}) {
return $self->{header_hash}{$key};
}
else {
return $Header::UNKNOWN_KEY;
}
}
sub Put_Tag {
my $self = shift;            # Objekttyp
my ($key,
$content) = @_;          # Uebergabeparameter	
return $Header::NOT_INITIALIZED
if $Header::init_status ==
$FALSE;
$self->{header_hash}{$key} = $content;
1;
}
sub Write_Header {
my $self = shift;		# hole Objektreferenz
my ($file,                  # Dateihandle
$orderlist_str) = @_;   # Reihenfolge der Schluesselwerte
return $Header::NOT_INITIALIZED
if $Header::init_status ==
$FALSE;
return $Header::FILEHANDLE_MISSING
if !defined( $file);
return $Header::LOCK_ERROR
unless flock $file, $LOCK_EX;
my @orderlist;
if ( defined( $orderlist_str)) {
@orderlist = split( /\s/, $orderlist_str);
} 
else {
@orderlist = keys( %{$self->{header_hash}}); 
}
print $file "# $self->{delimiter}\n";
my ( $key, $content);
foreach $key ( @orderlist) {
$content = $self->{header_hash}{$key};	
$content =~ s/\n/\n\#/g;
print $file "#\$$key:$content \$\n";
}
print $file "# $self->{delimiter}_END\n";
1;
}
sub Set_Free {
my $self = shift;		# hole Objektreferenz
my $file = shift;           # Dateihandle
return $Header::NOT_INITIALIZED
if $Header::init_status ==
$FALSE;
return $Header::FILEHANDLE_MISSING
if !defined( $file);
flock $file, $LOCK_UN;
}
sub Dump_All {
my $self = shift;		# hole Objektreferenz
my ($key,                   # Schluesselwert
$content);              # Inhalt
return $Header::NOT_INITIALIZED
if $Header::init_status ==
$FALSE;
print "Version: $Header::version\n";
while ( ($key, $content) = each (%{$self->{header_hash}}) ) {
print "$key:$content\n";
}
1;
}
1;
