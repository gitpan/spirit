package CIPP::DB_DBI_old;
use CIPP::DB_DBI;
@ISA = qw( CIPP::DB_DBI );
$VERSION  = "0.2";
sub new {
my ($type) = shift;
my ($db_name, $persistent) = @_;
my $self = $type->SUPER::new ($db_name, $persistent);
$self->{dbi_version} = '0.73';
return bless $self, $type;
}
1;
__END__
=head1 NAME
CIPP::DB_DBI_old - CIPP database module to generate old DBI (v0.73) code
=head1 DESCRIPTION
CIPP has a database code abstraction layer, so it can
generate code to access databases via different interfaces.
This module is used by CIPP to generate code to access
databases via DBI, version 0.73. (This is the version shipped
with Oracle Application Server 4.0)
=head1 AUTHOR
Jörn Reder, joern@dimedis.de
=head1 COPYRIGHT
Copyright 1997-1999 dimedis GmbH, All Rights Reserved
This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself.
=head1 SEE ALSO
perl(1), CIPP (3pm)
