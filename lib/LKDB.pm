package LKDB;
use strict;             # der normale Masochismus
use FileHandle;         # Objektmethoden fuer Dateihandles
my $db_module;
BEGIN {
if ( $^O =~ /win/i ) {
require "DB_File.pm";
$db_module = "DB_File";
} else {
require "GDBM_File.pm";
$db_module = "GDBM_File";
}
}
$LKDB::LOCK_SH = 1;     # shared Lock einer Datei
$LKDB::LOCK_EX = 2;     # exklusives Lock einer Datei
$LKDB::LOCK_UN = 8;     # loesen des Locks
$LKDB::version = "0.1.0.0";
sub new {
my $type = shift;
my ($filename, $lock_type) = @_;
$lock_type = 'ex' if ! defined $lock_type;
my $lock_num = -1;
$lock_num = $LKDB::LOCK_EX if $lock_type eq 'ex';
$lock_num = $LKDB::LOCK_SH if $lock_type eq 'sh';
if ( $lock_num == -1 ) {
return undef;
}
my $self = {};
my $fh = new FileHandle();
return undef if ! open ($fh, ">> $filename.lck");
return undef if ! flock ($fh, $lock_num);
if ( $db_module eq 'GDBM_File' ) {
return undef if ! tie ( %{$self->{hash}}, 'GDBM_File',
$filename, &GDBM_File::GDBM_WRCREAT, 0666);
} else {
return undef if ! tie ( %{$self->{hash}}, 'DB_File', 
$filename, O_CREAT|O_RDWR, 0660);
}
$self->{fh} = $fh;
return bless $self, $type;
}
sub DESTROY {
my $self = shift;
untie $self->{hash};
close $self->{fh};
}
1;
