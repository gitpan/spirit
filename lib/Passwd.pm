#!/usr/local/bin/perl -w
package Passwd;
use LkTyH;
@ISA = qw( LkTyH);           # Klasse LkTyH erben
$FILE_ERROR = -1;            # Datei konnte nicht geoeffnet werden
$UNKNOWN_USER = -2;          # Der spezifizierte Benutzer ist nicht eingetragen
$NOT_INITIALIZED = -3;       # Instanz konnte nicht erzeugt werden
$USER_ALREADY_CREATED = -4;  # Versuch bestehenden Benutzer noch einmal
$TRUE = 1;
$FALSE = 0;
$POS_PASSWD = 0;             # Position des Password-Strings im Zeileneintrag
$POS_FLAGS = 1;              # Position des Benutzerrechte-Strings im Zeileneintrag
$POS_PROJECTS = 2;           # Position des Projektzugehoerigkeits-Strings 
$version = "0.5.0";          # derzeitige Version der Klasse Passwd
$init_status = $TRUE;        # Status, ob eine Instanz erzeugt werden konnte
sub new {
my $type = shift;        # Objekttyp
my $filename = shift;    # Dateiname der Password-Datei
return undef if $init_status == $FALSE;
my $self = $type->SUPER::new( $filename);
$self->{passwd_hash} = \%{$self->{LkTyH_hash}};
if ($LkTyH::init_status == $FALSE) {
$init_status = $FALSE;
} 
return bless $self, $type;
} 
sub Create_User {
my $self = shift;            # Objekttyp
my ($username, 
$password, 
$flags, 
$projects) = @_;         # Uebergabeparameter	
return $NOT_INITIALIZED if $init_status == $FALSE;    
return $USER_ALREADY_CREATED if defined $self->{passwd_hash}{$username};
$self->Store_User( $username, $password, $flags, $projects);
$TRUE;
}
sub Modify_User {
my $self = shift;        # Objekttyp
my ($username, 
$password, 
$flags, 
$projects) = @_;     # Uebergabeparameter	
return $NOT_INITIALIZED if $init_status == $FALSE;    
return $UNKNOWN_USER unless defined $self->{passwd_hash}{$username};
$self->Store_User( $username, $password, $flags, $projects);
1;
}
sub Get_User {
my $self = shift;        # Objekttyp
my ($username, 
$flags, 
$projects) = @_;     # Uebergabeparameter	
return $NOT_INITIALIZED if $init_status == $FALSE;    
return $UNKNOWN_USER unless defined $self->{passwd_hash}{$username};
my $password;
( $password, $$flags, $$projects) = 
split( "\t", $self->{passwd_hash}{$username});
1;
}
sub Delete_User {
my $self = shift;           # Objekttyp
my $username = shift;       # Uebergabeparameter
return $UNKOWN_USER unless defined $self->{passwd_hash}{$username};
return $NOT_INITIALIZED if $init_status == $FALSE;
delete $self->{passwd_hash}{$username};
1;
}
sub Check_Project_Access {
my $self = shift;        # Objekttyp
my ($username, 
$project) = @_;      # Uebergabeparameter	
return $UNKOWN_USER unless defined $self->{passwd_hash}{$username};
return $NOT_INITIALIZED if $init_status == $FALSE;
my $projects = (split( "\t",
$self->{passwd_hash}{$username}))[$POS_PROJECTS];
if ( $projects =~ m/\s*($project)\s*/) {
return $TRUE;
} else {
return $FALSE;
}
}
sub Check_Admin_Access {
my $self = shift;        # Objekttyp
my ($username, 
$flag) = @_;         # Uebergabeparameter	
return $NOT_INITIALIZED if $init_status == $FALSE;
return $UNKNOWN_USER unless defined $self->{passwd_hash}{$username};
my $flags = (split( "\t", $self->{passwd_hash}{$username}))[$POS_FLAGS];
if ( $flags =~ m/\s*($flag)\s*/i) {
return $TRUE;
} else {
return $FALSE;
}
}
sub Check_Passwd {
my $self = shift;            # Objekttyp
my ($username, 
$password) = @_;         # Uebergabeparameter	
return $UNKNOWN_USER unless defined $self->{passwd_hash}{$username};
return $NOT_INITIALIZED if $init_status == $FALSE;
my $salt = 
substr $username, 0, 2;  # Stoerfaktor: zwei Zeichen
if ( $IDE::OS_has_crypt ) {
$password = crypt $password, $salt;    
}
$crypted_passwd = (split( "\t", 
$self->{passwd_hash}{$username}))[$POS_PASSWD];
if ( $password eq $crypted_passwd) {
return ( $TRUE);
} else {
return ( $FALSE);
}
}
sub Store_User {
my $self = shift;            # Objekttyp
my ($username, 
$password, 
$flags, 
$projects) = @_;         # Uebergabeparameter	
my $salt = 
substr $username, 0, 2;  # Stoerfaktor: zwei Zeichen
my @projectlist = 
split( "\t", $projects); # Projektliste
my @flaglist =
split( "\t", $flags);     # Flagliste
if ( $password eq "") {
$password = (split( "\t", 
$self->{passwd_hash}{$username}))[$POS_PASSWD];
}
else {
$password = crypt $password, $salt if $IDE::OS_has_crypt;
}
$self->{passwd_hash}{$username} = "$password\t".
join( ',', @flaglist)."\t".join( ",", @projectlist);
1;
}
sub Get_Userlist {
my $self = shift;        # Objekttyp
my $field = shift;       # Uebergabeparameter
my $username;            # Name der Benutzers
my %userhash;            # Hash der Benutzernamen
my %field_hash = (
PASSWORD => $POS_PASSWD,
RIGHTS => $POS_FLAGS,
PROJECTS => $POS_PROJECTS,
);
return $NOT_INITIALIZED if $init_status == $FALSE;
if ( $field eq 'USER') {
while ( ($username,$content) = each (%{$self->{passwd_hash}}) ) {
$userhash{$username} = $username;
}
}
else {
while ( ($username,$content) = each (%{$self->{passwd_hash}}) ) {
$userhash{$username} = 
(split( "\t", $content))[$field_hash{$field}];
}
}
return \%userhash;
}
sub Dump_All {
my $self = shift;		# hole Objektreferenz
my ($username, $content);
return $NOT_INITIALIZED if $init_status == $FALSE;
print "Version: $version\n";
while ( ($username, $content) = each (%{$self->{passwd_hash}}) ) {
print "$username:$content\n";
}
1;
}
1;
