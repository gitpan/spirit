package CIPP::DB_DBI;
$VERSION = "0.51_03";
$REVISION = q$Revision: 1.5.2.1 $;
use strict;
sub new {
my ($type) = shift;
my ($db_name, $persistent) = @_;
my $pkg = $db_name;
$pkg =~ s/^[^\.]+\.//;
$pkg =~ tr/./_/;
my $self = {
"db_name" => $db_name,
"pkg" => "\$cipp_db_$pkg",
"persistent" => $persistent,
"type" => undef,		# single | select,
"dbi_version" => '0.93'
};
return bless $self, $type;
}
sub Open {
my $self = shift;
my %arg = @_;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
my $back_prod_path = $self->{back_prod_path};
my $pkg_name = $pkg;
$pkg_name =~ s/\$//;
my $require;
if ( $arg{no_config_require} ) {
$require = "";
} else {
$require = qq{do "\$cipp::back_prod_path/config/${db_name}.db-conf"};
}
my $code;
if ( $self->{dbi_version} ne '0.73' ) {
$code = qq
[
use DBI;
$require;
if ( ${pkg}::dbh ) {
eval { ${pkg}::dbh->disconnect };
}
${pkg}::dbh = DBI->connect (
${pkg}::data_source,
${pkg}::user,
${pkg}::password,
{ PrintError => 0 } );
die "sql_open\t\$DBI::errstr" if \$DBI::errstr;
die "sql_open\tdbh is undef" if not ${pkg}::dbh;
]
} else {
$code = qq
[
use DBI;
$require;
my \$source = ${pkg}::data_source;
\$source =~ /^dbi:([^:]+)/;
\$source = \$1;
${pkg}::drh = DBI->install_driver(\$source);
die "sqlopen\tFehler bei DBI->install_driver" if \$DBI::errstr;
${pkg}::dbh = ${pkg}::drh->connect (
${pkg}::name,
${pkg}::user,
${pkg}::password
);
die "sql_open\t\$DBI::errstr" if \$DBI::errstr;
]
}
$code .= qq
[
if ( ${pkg}::data_source !~ /mysql/ ) {
${pkg}::dbh->{AutoCommit} = ${pkg}::Auto_Commit;
}
];
return $code;
}
sub Close {
my $self = shift;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
my $code = qq[eval{\n].
qq[if ( ${pkg}::dbh and not ${pkg}::dbh->{AutoCommit} ) {\n].
qq[\t${pkg}::dbh->rollback;\n}\n];
if ( not $self->{persistent} ) {
$code .= "${pkg}::dbh->disconnect() if ${pkg}::dbh;\n${pkg}::dbh=undef;\n";
} else {
$code .= "# persistence: no dbh->disconnect\n";
}
$code .= "\n};\n";
return $code;
}
sub Begin_SQL {
my $self = shift;
my ($sql, $result, $throw, $maxrows, $winstart, $winsize,
$gen_my, $input_lref, @var) = @_;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
$sql =~ s/;$//;
my ($code, $var, $maxrows_cond, $winstart_cmd);
$maxrows_cond='';
$winstart_cmd='';
my $fetch_method = $self->{dbi_version} eq '0.73' ?
'fetch' : 'fetchrow_arrayref';
my $bind_list = '';
if ( scalar (@{$input_lref}) ) {
$bind_list = join (",", @{$input_lref});
}
if ( defined $var[0] ) {
$code =  qq {my (${pkg}_sth, ${pkg}_ar, ${pkg}_maxrows, ${pkg}_winstart);};
$self->{type} = "select";
$var = "\$".join (", \$", @var);
$code .= qq {my ($var);\n} if $gen_my;
$code .= qq {${pkg}_sth = }.
qq {${pkg}::dbh->prepare ( qq{$sql} );}."\n".
qq {die "$throw\t\$DBI::errstr" if \$DBI::errstr;}. "\n";
$code .= qq {${pkg}_sth->execute($bind_list);}."\n".
qq {die "$throw\t\$DBI::errstr" if defined \$DBI::errstr;}."\n";
if ( defined $maxrows ) {
$code .= qq {${pkg}_maxrows=$maxrows;\n};
$maxrows_cond = "${pkg}_maxrows-- > 0 and";
}
if ( defined $winstart ) {
$code .= qq {${pkg}_maxrows=$winstart+$winsize;\n};
$code .= qq {${pkg}_winstart=$winstart;\n};
$maxrows_cond = "--${pkg}_maxrows > 0 and";
$winstart_cmd =
qq {next if --${pkg}_winstart }.
qq {> 0;\n};
}
$code .= qq [SQL: while ( $maxrows_cond ${pkg}_ar = ].
qq [${pkg}_sth->$fetch_method ) {]."\n";
$code .= qq [$winstart_cmd($var) = \@{${pkg}_ar};]."\n";
} else {
if ( $bind_list ne '' ) {
$bind_list = ", undef, $bind_list";
}
$self->{type} = "single";
if ( defined $result ) {
$result = "\$".$result if $result !~ /^\$/;
$code = '';
$code = 'my ' if $gen_my;
$code .= qq{$result = };
}
$code .= qq{${pkg}::dbh->do( qq{$sql} $bind_list);}."\n";
$code .= qq{die "$throw\t\$DBI::errstr" if defined \$DBI::errstr;}."\n";
}
return $code;
}
sub End_SQL {
my $self = shift;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
if ( $self->{type} eq "select" ) {
return qq(}\n${pkg}_sth->finish;\n)
} else {
return "";
}
}
sub Quote_Var {
my $self = shift;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
my ($var, $db_var, $gen_my) = @_;
my $code = '';
$code = qq{my $db_var;\n} if $gen_my;
$code .= qq{$var = undef if $var eq '';}."\n";
$code .= qq{$db_var = ${pkg}::dbh->quote($var);}."\n";
return $code;
}
sub Commit {
my $self = shift;
my ($throw) = @_;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
my $code = '';
$code .= qq[if ( ${pkg}::data_source !~ /mysql/ ) {\n];
$code .= qq{${pkg}::dbh->commit();}."\n";
$code .= qq{die "$throw\t\$DBI::errstr" if defined \$DBI::errstr;}."\n";
$code .= qq[}\n];
return $code;
}
sub Rollback {
my $self = shift;
my ($throw) = @_;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
my $code;
$code  = qq{${pkg}::dbh->rollback();}."\n";
$code .= qq{die "$throw\t\$DBI::errstr" if defined \$DBI::errstr;}."\n";
return $code;
}
sub Autocommit {
my $self = shift;
my ($status, $throw) = @_;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
my $code = '';
$code .= qq[if ( ${pkg}::data_source !~ /mysql/ ) {\n];
if ( $status == 0 ) {
$code .= qq{${pkg}::dbh->{AutoCommit}=0;}."\n";
} else {
$code .= qq{${pkg}::dbh->{AutoCommit}=1;}."\n";
}
$code .= qq[}\n];
return $code;
}
sub Get_DB_Handle {
my $self = shift;
my ($var, $my) = @_;
my $db_name = $self->{db_name};
my $pkg = $self->{pkg};
$var = "my $var" if $my;
my $code  = qq{$var = ${pkg}::dbh;}."\n";
return $code;
}
1;
__END__
=head1 NAME
CIPP::DB_DBI - CIPP database module to generate DBI code
=head1 DESCRIPTION
CIPP has a database code abstraction layer, so it can
generate code to access databases via different interfaces.
This module is used by CIPP to generate code to access
databases via DBI, version >= 0.93.
=head1 AUTHOR
Jörn Reder, joern@dimedis.de
=head1 COPYRIGHT
Copyright 1997-1999 dimedis GmbH, All Rights Reserved
This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself.
=head1 SEE ALSO
perl(1), CIPP (3pm)
