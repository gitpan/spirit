package CIPP::DB_Sybase;
$VERSION = "0.2";
sub new {
my ($type) = shift;
my ($db_name, $back_prod_path) = @_;
my $pkg;	
($pkg = $db_name) =~ tr/./_/;
my $self = {
"db_name" => $db_name,
"pkg" => "\$cipp_db_$pkg",
"back_prod_path" => $back_prod_path,
"type" => undef		# single | select
};
return bless $self, $type;
}
sub Open {
my $self = shift;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
my $back_prod_path = $self->{back_prod_path};
my $pkg_wo_d = $pkg;	# Variable $pkg_wo_d ist gleich $pkg,
$pkg_wo_d =~ s/\$//;	# nur 'without dollar' :)
my $code = qq[;
use Sybase::CTlib;
my \$close_connection;
if ( ! defined ${pkg}::dbh ) {
require '$back_prod_path/config/${db_name}.db-conf';
${pkg}::dbh = new Sybase::CTlib ${pkg}::user, ${pkg}::password,
${pkg}::system;
die "connect_database\tCannot connect to ${pkg}::system" if ! defined ${pkg}::dbh;
\$close_connection = 1;
ct_callback (CS_CLIENTMSG_CB, \\&${pkg_wo_d}::msg_client_cb);
ct_callback (CS_SERVERMSG_CB, \\&${pkg_wo_d}::msg_server_cb);
${pkg}::Begin_Work = 0;
${pkg}::errstr = undef;
${pkg}::dbh->ct_sql("use ${pkg}::name");
die "use_database\tuse ${pkg}::name fails" if defined ${pkg}::errstr;
}
sub ${pkg_wo_d}::msg_client_cb {
my(\$layer, \$origin, \$severity, \$number, \$msg, \$osmsg) = \@_;
return CS_SUCCEED if \$severity <= 10;
my \$text;
\$text = "Open Client Message: ";
\$text .= sprintf "Message number: LAYER = (%ld) ORIGIN = (%ld) ",
\$layer, \$origin;
\$text .= sprintf "SEVERITY = (%ld) NUMBER = (%ld) - ",
\$severity, \$number;
\$text .= sprintf "Message String: %s - ", \$msg;
if (defined(\$osmsg)) {
\$text .= sprintf "Operating System Error: %s", \$osmsg;
}
${pkg}::errstr = \$text;
return CS_SUCCEED;
}
sub ${pkg_wo_d}::msg_server_cb {
my(\$cmd, \$number, \$severity, \$state, \$line, \$server,
\$proc, \$msg) = \@_;
return CS_SUCCEED if \$severity <= 10;
my \$text;
\$text = "Server message: ";
\$text .= sprintf "Message number: %ld, Severity %ld, ",
\$number, \$severity;
\$text .= sprintf "State %ld, Line %ld - ", \$state, \$line;
if (defined(\$server)) {
\$text .= sprintf "Server '%s' - ", \$server;
}
if (defined(\$proc)) {
\$text .= sprintf " Procedure '%s' - ", \$proc;
}
\$text .= sprintf "Message String: %s", \$msg;
${pkg}::errstr = \$text;
return CS_SUCCEED;
}
];
return $code;
}
sub Close {
my $self = shift;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
my $code = qq [if ( ${pkg}::Begin_Work ) {\n].
qq [${pkg}::errstr = undef;\n].
qq [${pkg}::dbh->ct_sql('rollback');\n].
qq [die ${pkg}::errstr if ${pkg}::errstr;\n}\n].
qq [${pkg}::dbh = undef if defined \$close_connection;\n];
return $code;
}
sub Begin_SQL {
my $self = shift;
my ($sql, $result, $throw, $maxrows, $winstart, $winsize,
$gen_my, $input_lref, @var) = @_;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
$self->{throw} = $throw;
$sql =~ s/;$//;
my ($code, $var, $maxrows_cond, $winstart_cmd);
$maxrows_cond='';
$winstart_cmd='';
$code = qq [if ( ! ${pkg}::Auto_Commit and ! ${pkg}::Begin_Work ) {\n].
qq [${pkg}::errstr = undef;\n].
qq [${pkg}::dbh->ct_sql ('begin transaction');\n].
qq [die "$throw\t".${pkg}::errstr if ${pkg}::errstr;\n].
qq [${pkg}::Begin_Work = 1;\n}\n];
if ( defined $var[0] ) {
$self->{type} = "select";
$var = "\$".join (", \$", @var);
$code .=  qq [${pkg}::errstr = undef;\n${pkg}::sth = ].
qq [${pkg}::dbh->ct_execute ( qq{$sql} );\n].
qq [die "$throw\t".${pkg}::errstr if ${pkg}::errstr;\n];
if ( defined $maxrows ) {
$code .= qq {${pkg}::maxrows=$maxrows;\n};
$maxrows_cond = "${pkg}::maxrows-- > 0 and";
}
if ( defined $winstart ) {
$code .= qq {${pkg}::maxrows=$winstart+$winsize\n};
$code .= qq {${pkg}::winstart=$winstart;\n};
$maxrows_cond = "--${pkg}::maxrows > 0 and";
$winstart_cmd =
qq {next if --${pkg}::winstart }.
qq {> 0;\n};
}
$code .= qq [while ( $maxrows_cond ].
qq [${pkg}::dbh->ct_results(\$main::restype) == CS_SUCCEED ) {\n].
qq [next unless ${pkg}::dbh->ct_fetchable(\$main::restype);\n].
qq [if ( \$main::restype != CS_ROW_RESULT ) { ].
qq [${pkg}::dbh->ct_cancel (CS_CANCEL_ALL); } else {\n].
qq [while ( ${pkg}::ar = ${pkg}::dbh->ct_fetch(0,1) ) {\n].
qq [($var) = \@{${pkg}::ar};\n];
} else {
$self->{type} = "single";
$code .= qq [${pkg}::errstr = undef;\n].
qq [${pkg}::dbh->ct_sql( qq{$sql} );\n].
qq [die "$throw\t".${pkg}::errstr if ${pkg}::errstr;\n];
}
return $code;
}
sub End_SQL {
my $self = shift;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
my $throw = $self->{throw};
if ( $self->{type} eq "select" ) {
return  qq [}}}\n].
qq [die "$throw\t".${pkg}::errstr if ${pkg}::errstr;\n];
} else {
return "";
}
}
sub Quote_Var {
my $self = shift;
my $pkg = $self->{pkg};
my ($var, $db_var) = @_;
$code = qq [if ( $var eq '' ) {\n].
qq [$db_var = 'NULL';\n].
qq [} else {\n].
qq [($db_var = $var) =~ s/'/''/g;\n].
qq [$db_var="'".$db_var."'";\n}\n];
return $code;
}
sub Commit {
my $self = shift;
my ($throw) = @_;
my $pkg = $self->{pkg};
my $code = qq [if ( ${pkg}::Auto_Commit ) {\n].
qq [die "$throw\tCOMMIT: nicht moeglich bei AUTOCOMMIT=ON";\n].
qq [} elsif ( ! ${pkg}::Begin_Work ) {\n].
qq [die "$throw\tCOMMIT: nicht in einer Transaktion";\n].
qq [} else {\n].
qq [${pkg}::errstr = undef;\n].
qq [${pkg}::dbh->ct_sql('commit');\n].
qq [die "$throw\t".${pkg}::errstr if defined ${pkg}::errstr;\n].
qq [${pkg}::Begin_Work = 0;\n}\n];
return $code;
}
sub Rollback {
my $self = shift;
my ($throw) = @_;
my $pkg = $self->{pkg};
my $code  = qq [if ( ${pkg}::Auto_Commit ) {\n].
qq [die "$throw\tROLLBACK: nicht moeglich bei AUTOCOMMIT=ON;"\n].
qq [} elsif ( ! ${pkg}::Begin_Work ) {\n].
qq [die "$throw\tROLLBACK: nicht in einer Transaktion";\n].
qq [} else {\n].
qq [${pkg}::errstr = undef;\n].
qq [${pkg}::dbh->ct_sql('rollback');\n].
qq [die "$throw\t".${pkg}::errstr if defined ${pkg}::errstr;\n].
qq [${pkg}::Begin_Work = 0;\n}\n];
return $code;
}
sub Autocommit {
my $self = shift;
my ($status, $throw) = @_;
my $pkg = $self->{pkg};
my $code = qq [if ( ! ${pkg}::Begin_Work ) {\n].
qq [${pkg}::Auto_Commit = $status;\n].
qq [} else {\n].
qq [die "$throw\tAUTOCOMMIT: Umschalten in einer TA nicht moeglich";\n}\n];
return $code;
}
sub Get_DB_Handle {
my $self = shift;
my ($var, $my) = @_;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
$var = "my $var" if $my;
$code  = qq{$var = ${pkg}::dbh;}."\n";
return $code;
}
1;
__END__
=head1 NAME
CIPP::DB_DBI - CIPP database module to generate Sybperl code
=head1 DESCRIPTION
CIPP has a database code abstraction layer, so it can
generate code to access databases via different interfaces.
This module is used by CIPP to generate code to access
databases via Sybperl.
=head1 AUTHOR
Jörn Reder, joern@dimedis.de
=head1 COPYRIGHT
Copyright 1997-1999 dimedis GmbH, All Rights Reserved
This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself.
=head1 SEE ALSO
perl(1), CIPP (3pm)
