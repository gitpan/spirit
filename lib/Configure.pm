#!/usr/local/bin/perl 
package Configure;
use Struct_File;
@ISA = qw( Struct_File);     # Klasse Struct_File erben
$NOT_INITIALIZED = -3;       # Instanz konnte nicht erzeugt werden
$TRUE = 1;
$FALSE = 0;
$version = "0.2.0";          # derzeitige Version der Klasse Driver
sub new {
my $type = shift;        # Objekttyp
my $filename = shift;    
my $username = shift;    # Uebergabeparameter
return undef if $Struct_File::init_status == $FALSE;
my $self = $type->SUPER::new( $filename);
$self->{username} = $username;
return bless $self, $type;
}
sub Delete {
my $self = shift;           # Objekttyp
return $NOT_INITIALIZED if $Struct_File::init_status == $FALSE;
$self->SUPER::Delete( $self->{username});
unlink "$IDE::Config_Dir/$self->{username}.pl";
}
sub DESTROY {
my $self = shift;           # Objekttyp
return $NOT_INITIALIZED if $Struct_File::init_status == $FALSE;
my ($item,                  # Schluesselwort
$content,               # Inhalt des entsprechenden Schluesselwortes
$cnf_hash_ref,          # Hash mit den Konfigurationsparametern
$fh);                   # Filehandle der Benutzerkonfigurationsdatei
$cnf_hash_ref = $self->Get_Items( $self->{username});    
if ( defined %$cnf_hash_ref) {
$fh = new FileHandle ">$IDE::Config_Dir/$self->{username}.pl";  
print $fh "package USER;\n\n";
while ( ( $item, $content) = each( %{$cnf_hash_ref})) {
print $fh "\$$item = \"$content\";\n";
}
}
$self->SUPER::DESTROY();
}
1;
