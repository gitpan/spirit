#!/usr/local/bin/perl -w
package IDE_Header;
use Header;                  # Basisklasse
use Text::Wrap;              # Modul mit Textformatfunktionen
use Text::Tabs;              # Modul zur Tabulatorformatierung
use strict;
@IDE_Header::ISA = qw( Header);          # Klasse Header erben
$IDE_Header::FILEHANDLE_MISSING = -1;    # Dateizeiger ist nicht gueltig
$IDE_Header::UNKNOWN_KEY = -2;           # Schluesselwort ist nicht bekannt
$IDE_Header::NOT_INITIALIZED = -3;       # Instanz konnte nicht erzeugt werden
$IDE_Header::ORDERLIST_NOT_COMPLETE =-4; # fehlender Eintrag in der Orderliste
my $TRUE = 1;
my $FALSE = 0;
$IDE_Header::version = "0.3.0";          # derzeitige Version der Klasse Header
$IDE_Header::init_status = $TRUE;        # Status, ob eine Instanz erzeugt werden konnte
my $IDE_orderlist = "OBJECT_VERSION\nOBJECT_NAME\nOBJECT_TYPE\nDESCRIPTION\n".
"COPYRIGHT\nLAST_MODIFY_BY\nLAST_MODIFY_DATE\nMODIFICATION_HISTORY\t";
my $spaces = 25;                # Absatzeinrueckung
sub new {
my $type = shift;        # Objekttyp
my ($file,               # Dateihandle
$order_str) = @_;    # Reihenfolge der benutzerdefinierten
return undef if $IDE_Header::init_status == $FALSE;
my $self;                # Instanz-Hash fuer Instanzvariablen
$self = $type->SUPER::new( $file, 'IDE_HEADER');
if ($Header::init_status ==
$FALSE) {
$IDE_Header::init_status = $FALSE;
} 
else {    	
$order_str ||= '';
$self->{IDE_orderlist} = $IDE_orderlist . $order_str;
if ( defined( $file)) {
my $fehler = $self->Check_Orderlist();
$IDE_Header::init_status = 
$IDE_Header::ORDERLIST_NOT_COMPLETE unless $fehler == $TRUE;
}
}
return bless $self, $type;
}
sub Get_Tag {
my $self = shift;            # Objekttyp
my ($key) = @_;              # Uebergabeparameter	
my ($content);               # Inhalt des angegebenen Schluessels
return $IDE_Header::NOT_INITIALIZED if $Header::init_status ==
$FALSE;
if ( $IDE::cvs ) {
return "42.0.0.1"                if $key eq 'OBJECT_VERSION';
return "wem?"                    if $key eq 'LAST_MODIFY_BY';
return "01.01.2000-00:00:00"     if $key eq 'LAST_MODIFY_DATE';
return "no history, future only" if $key eq 'MODIFICATION_HISTORY';
}
$content = $self->SUPER::Get_Tag( $key);
if ( $content ne $Header::UNKNOWN_KEY) {
$IDE_orderlist =~ m/[\n\t]*$key([\n\t])/;
my $delimiter = $1 || '';
if ( $delimiter ne "\t") {
$content =~ s/^\s+//;
$content =~ s/\s+/ /g;
}
else {
$content =~ s/[ \t]+/ /g;
$content =~ s/\n /\n/g;
$content =~ s/^ //;
}
}
return  $content;
}
sub Put_Tag {
my $self = shift;            # Objekttyp
my ($key,
$content) = @_;          # Uebergabeparameter	
return $IDE_Header::NOT_INITIALIZED if $IDE_Header::init_status == $FALSE;
if ( $IDE::cvs ) {
$content = "42.0.0.1"                if $key eq 'OBJECT_VERSION';
$content = "wem?"                    if $key eq 'LAST_MODIFY_BY';
$content = "01.01.2000-00:00:00"     if $key eq 'LAST_MODIFY_DATE';
$content = "no history, future only" if $key eq 'MODIFICATION_HISTORY';
}
return $IDE_Header::UNKNOWN_KEY 
unless $self->{IDE_orderlist} =~ m/[\n\t]*$key([\n\t])/;
my $pre1 = " " x ($spaces - length("\$$key:"));
$content ||= "";
$content = "\$$key:$pre1" . $content;
if ( $1 ne "\t") {	
my $pre2 = " " x $spaces;
$content = wrap( '', $pre2, $content);
}
else {
my $sp = " " x $spaces;
$content =~ s/\n/\n$sp/g;
$content = unexpand( $content);
}
$content =~ s/^\$$key://;	
$self->SUPER::Put_Tag( $key, $content);
1; 
}
sub Write_IDE_Header {
my $self = shift;		# hole Objektreferenz
my $file = shift;           # Dateihandle
return $IDE_Header::NOT_INITIALIZED if $IDE_Header::init_status == $FALSE;
return $IDE_Header::FILEHANDLE_MISSING if !defined( $file);
my $fehler = $self->Check_Orderlist();
return $fehler unless $fehler == $TRUE;
$self->Write_Header( $file, $self->{IDE_orderlist});
1;
}
sub Check_Orderlist {
my $self = shift;		# hole Objektreferenz    
return 1;
my $key;                    # Schluesselwert
my @order_list = split( /[\t\n]/, $self->{IDE_orderlist});
foreach $key (@order_list) {
print STDERR "checke $key ";
if ( $self->SUPER::Get_Tag( $key) eq 
$Header::UNKNOWN_KEY ) {
print STDERR "fehlt!\n";
return $IDE_Header::ORDERLIST_NOT_COMPLETE;
}
print STDERR "ok\n";
}
1;
}
1;
