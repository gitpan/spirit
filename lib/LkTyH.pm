#!/usr/local/bin/perl -w
package LkTyH;
use FileHandle;              # Objektmethoden fuer Dateihandles
use SDBM_File;               # Aus Kompatibilitaetsgruenden zu WIN95
use Fcntl;                   # fuer File-Locking
$NOT_INITIALIZED = -3;       # Instanz konnte nicht erzeugt werden
$LOCK_EX = 2;                # exklusives Sperren einer Datei
$LOCK_UN = 8;                # loesen der Sperre
$TRUE = 1;
$FALSE = 0;
$version = "0.1.0";          # derzeitige Version der Klasse 
$init_status = $TRUE;        # Status, ob eine Instanz erzeugt werden konnte
sub new {
my $type = shift;        # Objekttyp
my $filename = shift;    # Dateiname
my $self = {};	     # Instanz-Hash fuer Instanzvariablen
return undef if $init_status == $FALSE;
my $lockfile = $filename . '.lock';
$self->{fh} = new FileHandle ">$lockfile";
if ( defined $self->{fh} ) {
if ( flock( $self->{fh}, $LOCK_EX)) {
tie ( %{$self->{LkTyH_hash}}, 'SDBM_File', 
$filename, O_CREAT|O_RDWR, 0660)
or $init_status = $FALSE;
} else {
$init_status = $FALSE;
}	
} 
else {
$init_status = $FALSE;
}
return bless $self, $type;
} 
sub DESTROY {
my $self = shift;        # Objektreferenz
return if $init_status == $FALSE;
untie $self->{LkTyH_hash};
flock $self->{fh}, $LOCK_UN;
undef $self->{fh};       # Schliesst die datei automatisch
}
1;
