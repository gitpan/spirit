#!/usr/local/bin/perl -w
package Struct_File;
use LkTyH;
@ISA = qw( LkTyH);           # Klasse LkTyH erben
$NOT_INITIALIZED = -3;       # Instanz konnte nicht erzeugt werden
$TRUE = 1;
$FALSE = 0;
$version = "0.2.0";          # derzeitige Version der Klasse
$init_status = $TRUE;        # Status, ob eine Instanz erzeugt werden konnte
sub new {
my $type = shift;        # Objekttyp
my $filename = shift;    # Dateiname der Password-Datei
return undef if $init_status == $FALSE;
my $self = $type->SUPER::new( $filename);
$self->{struct_file_hash} = \%{$self->{LkTyH_hash}};
if ($LkTyH::init_status == $FALSE) {
$init_status = $FALSE;
return undef;
} 
return bless $self, $type;
} 
sub Get_List {
my $self = shift;        # Objekttyp
my $field = shift;       # Eintrag
my ($string, $drv); 
return $NOT_INITIALIZED if $init_status == $FALSE;    
my ($key, $item, $struct_file, $collected, @struct_file_list);
$collected = '';
foreach $key ( keys %{$self->{struct_file_hash}} ) {
($struct_file = $key) =~ s/_.+$//;
if ( $collected !~ m/\t$struct_file\t/ ) {
push @struct_file_list, $struct_file ;
$collected .= "\t$struct_file\t";
}
}
my %field_hash;
foreach $item ( @struct_file_list ) {
$field_hash{$item} = $self->{struct_file_hash}{"${item}_$field"};
} 
return \%field_hash;
}
sub Get_Items {
my $self = shift;        # Objekttyp
my $item = shift;        # Oberbegriff
return $NOT_INITIALIZED if $init_status == $FALSE;    
my %item_hash;
my $key;
foreach $key ( keys %{$self->{struct_file_hash}} ) {
if ( $key =~ m/^($item)_(.*)/) {
my $new_key = $2;
$item_hash{$new_key} = $self->{struct_file_hash}{$key}
}
}
return \%item_hash;
}
sub Read {
my $self = shift;            # Objekttyp
my ($item,    
$field ) = @_;             # Uebergabeparameter	
return $NOT_INITIALIZED if $init_status == $FALSE;    
return $self->{struct_file_hash}{"${item}_$field"};
1;
}
sub Write {
my $self = shift;            # Objekttyp
my ($item,    
$field,
$content ) = @_;         # Uebergabeparameter	
return $NOT_INITIALIZED if $init_status == $FALSE;    
$self->{struct_file_hash}{"${item}_$field"} = $content;
1;
}
sub Delete {
my $self = shift;           # Objekttyp
my $item = shift;         # Uebergabeparameter
return $NOT_INITIALIZED if $init_status == $FALSE;
my ($key, $val);
foreach $key ( keys %{$self->{struct_file_hash}} ) {
if ( $key =~ /^$item/ ) {
delete $self->{struct_file_hash}{$key};
}
}
1;
}
1;
