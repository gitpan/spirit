#!/usr/bin/perl
BEGIN {
unshift (@INC, '../../lib') if -d '../../lib';
unshift (@INC, '../../../lib') if -d '../../../lib';
}
use strict;
use Param;
use File::Copy;
use Config;
my $OS;
main: {
$OS = $Config::Config{'osname'};
if ( $OS =~ /win/i ) {
$main::temp_dir = "C:/TEMP";
} else {
$main::temp_dir = "/tmp";
}
my $par = Input();
my $result = Check_Parameter ($par);
if ( ! $result ) {
my $db_type = $par->{DB_TYPE};
if ( $db_type eq 'Informix' ) {
$result = SQL_Informix ($par);
} elsif ( $db_type eq 'Sybase' )  {
$result = SQL_Sybase ($par);
} elsif ( $db_type eq 'Oracle'){
$result = SQL_Oracle ($par);
} elsif ( $db_type eq 'mysql' ){
$result = SQL_MySQL ($par);
} else {
$result = {
'success'	=>	'no',
'errno'		=>	4
};
}
}
Output ($result);
}
sub Input {
my $buffer = $ENV{SEP_INPUT};
return Scalar2Hash (\$buffer);
}
sub Output {
my ($href) = @_;
print ${Hash2Scalar ($href)};
}
sub Check_Parameter {
my ($par) = @_;
if ( ! defined $par ) {
return {
'success'	=>	'no',
'errno'		=>	1
};
}
my %needed = qw {
DB_SYSTEM 0 DB_NAME 0 DB_USER 0 DB_PASS 0
DB_CMD 0 DB_TYPE 0 SQL_FILE 0 OUTPUT_FILE 0
};
my @missing;
my $needed;
foreach $needed (keys %needed) {
if ( ! defined $par->{$needed} ) {
push @missing, $needed;
}
}
if ( scalar @missing ) {
return {
'success'	=>	'no',
'errmsg'	=>	join (", ",@missing),
'errno'		=>	3
};
}
my @unknown;
my $p;
foreach $p ( keys (%{$par}) ) {
if ( ! defined $needed{$p} ) {
push @unknown, $p;
}
}
if ( scalar @unknown ) {
return {
'success'	=>	'no',
'errmsg'	=> 	join (", ", @unknown),
'errno'		=>	2
};
}
if ( ! -f $par->{SQL_FILE} ) {
return {
'success'	=>	'no',
'errno'		=>	5
};
}
my $sqlbin = $par->{DB_CMD};
$sqlbin =~ s/\s.*$//;
if ( ! -f $sqlbin ) {
return {
'success'	=>	'no',
'errno'		=>	100
};
}
if ( ! -x $sqlbin ) {
return {
'success'	=>	'no',
'errno'		=>	101
};
}
open (OUTPUT, "> ".$par->{OUTPUT_FILE})
or return {
'success'	=>	'no',
'errno'		=>	6
};
close OUTPUT;
return undef;
}
sub SQL_Informix {
my ($href) = @_;
my $full_db_name = $href->{DB_NAME}.'@'.$href->{DB_SYSTEM};
my $db_user      = $href->{DB_USER};
my $db_pw        = $href->{DB_PASS};
my $output_file  = $href->{OUTPUT_FILE};
my $sql_file     = $href->{SQL_FILE};
my $tmp_file = "$main::temp_dir/sep$$.sql";
open (SQL, $sql_file);
open (TMP, "> $tmp_file") or
return {
"success"	=>	"no",
"errmsg"	=>	"can't write $tmp_file"
};
print TMP "connect to '$full_db_name' user '$db_user' using '$db_pw';\n";
while (<SQL>) {
print TMP;
}
close SQL;
close TMP;
my $db_cmd = $href->{DB_CMD}. " -e - $tmp_file 2>&1";
if ( $OS =~ /win/i ) {
$db_cmd =~ s!/!\\!g;
}
open (CMD, "$db_cmd |") or die "can't fork $db_cmd";
open (OUT, "> $output_file") or die "can't write $output_file";
my $first = 1;
while (<CMD>) {
print OUT if not $first;
$first = 0;
}
close OUT;
close CMD;
unlink $tmp_file;
return {
'success'	=>	'yes'
};
}
sub SQL_MySQL {
my ($href) = @_;
my $db_name     = $href->{DB_NAME};
my $db_system   = $href->{DB_SYSTEM};
my $db_user     = $href->{DB_USER};
my $db_pw       = $href->{DB_PASS};
my $output_file = $href->{OUTPUT_FILE};
my $sql_file    = $href->{SQL_FILE};
my $db_cmd = $href->{DB_CMD}.
" -v -v -v -f -h$db_system -u$db_user -p$db_pw".
" $db_name < $sql_file > $output_file 2>&1";
system ($db_cmd);
return {
'success'	=>	'yes'
};
}
sub SQL_Sybase {
my ($href) = @_;
my $db_system    = $href->{DB_SYSTEM};
my $db_name      = $href->{DB_NAME};
my $db_user      = $href->{DB_USER};
my $db_pw        = $href->{DB_PASS};
my $output_file  = $href->{OUTPUT_FILE};
my $sql_file     = $href->{SQL_FILE};
my $tmp_file = "$main::temp_dir/sep$$.sql";
open (SQL, $sql_file);
open (TMP, "> $tmp_file") or
return {
"success"	=>	"no",
"errmsg"	=>	"can't write $tmp_file"
};
print TMP "use $db_name\ngo\n";
while (<SQL>) {
print TMP;
}
close SQL;
close TMP;
my $db_cmd = $href->{DB_CMD}." -e ".
"-U$db_user -P$db_pw -S$db_system ".
"< $tmp_file > $output_file 2>&1";
system ($db_cmd);
unlink $tmp_file;
return {
'success'	=>	'yes'
};
}
sub SQL_Oracle {
my ($href) = @_;
my $cmd         = $href->{DB_CMD};
my $db_name     = $href->{DB_NAME};
my $db_system   = $href->{DB_SYSTEM};
my $db_user     = $href->{DB_USER};
my $db_pw       = $href->{DB_PASS};
my $output_file = $href->{OUTPUT_FILE};
my $sql_file    = $href->{SQL_FILE};
rename $sql_file, $sql_file.".sql";
if ( $Config{osname} =~ /win/i ) {
$cmd =~ s!/!\\!g;
$output_file =~ s!/!\\!g;
$sql_file =~ s!/!\\!g;
}
$cmd .= " $db_user/$db_pw\@$db_name";
open (DB, "| $cmd > $output_file 2>&1") or die "can't fork $cmd";
print DB "set echo on\n\@$sql_file\n";
close DB;
rename $sql_file.".sql", $sql_file;
return {
'success'	=>	'yes'
};
}
