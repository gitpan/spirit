#!/usr/local/bin/perl
if ( 0 ) {
print "Testlauf:\n\n";
print "Schreibe in Datei mit dem Namen 'testdatei1.txt'...\n";
$h1 = new CIPP::OutputHandle ('testdatei1.txt');
print "Status: ", $h1->Get_Init_Status(),"\n";
$h1->Write ("das ist ein Test 1\n");
$h1->Write ("das war's auch schon\n");
$h1 = undef;
print "\nSchreibe ueber Handle in Datei 'testdatei2.txt'...\n";
open (RAUS, "> testdatei2.txt") or die;
$h2 = new CIPP::OutputHandle (\*RAUS);
print "Status: ", $h2->Get_Init_Status(),"\n";
$h2->Write ("das ist ein Test 2\n");
$h2->Write ("das war's auch schon\n");
$h2 = undef;
print "\nSchreibe in Memory...\n";
my $memory = '';
$h3 = new CIPP::OutputHandle (\$memory);
print "Status: ", $h3->Get_Init_Status(),"\n";
$h3->Write ("das ist ein Test 3\n");
$h3->Write ("das war's auch schon\n");
$h3 = undef;
print "Im Memory steht:\n$memory\n";
exit;
}
package CIPP::OutputHandle;
$CIPP::OutputHandle::obj_nr = 0;
$VERSION = "0.2";
sub new {
my $type = shift;
my ($output) = @_;
my $init_status = 1;
my $filehandle;
my $buffer;
$CIPP::OutputHandle::obj_nr++;
if ( ref $output eq 'GLOB' ) {
$buffer_ref = undef;
$filehandle = $output;
my $test_filehandle = print $filehandle '';
$init_status = 0 if ! defined $test_filehandle;
} elsif ( ref $output eq 'SCALAR' ) {
$filehandle = undef;
$buffer_ref = $output;
} elsif (not ref $output ) {
$filehandle = "OutputHandle".$CIPP::OutputHandle::obj_nr;
open ($filehandle, "> $output") || ($init_status=0);
$buffer_ref = undef;
} else {
$filehandle = undef;
$buffer_ref = undef;
$init_status = 0;
}
my $self = {
"filehandle" => $filehandle,
"buffer_ref" => $buffer_ref,
"init_status" => $init_status,
"obj_nr" => $CIPP::OutputHandle::obj_nr
};
return bless $self, $type;
}
sub DESTROY {
my $self = shift;
if ( defined $self->{filehandle} ) {
my $filehandle = $self->{filehandle};
close $filehandle;
}
}
sub Get_Init_Status {
my $self = shift;
return $self->{init_status};
}
sub Write {
my $self = shift;
return undef if ! $self->{init_status};
my ($output) = @_;
if ( defined $self->{filehandle} ) {
my $filehandle = $self->{filehandle};
return print $filehandle $output;
} else {
${$self->{buffer_ref}} .= $output;
return 1;
}
}
1;
__END__
=head1 NAME
CIPP::OutputHandle - Output stream abstraction (file and memory I/O)
=head1 DESCRIPTION
This module abstracts from an output target. So it is possible to
write transparently to a file, filehandle or into memory.
=head1 AUTHOR
Jörn Reder, joern@dimedis.de
=head1 COPYRIGHT
Copyright 1997-1999 dimedis GmbH, All Rights Reserved
This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself.
=head1 SEE ALSO
perl(1), CIPP (3pm)
