#!/usr/local/bin/perl
if ( 0 ) {
print "Datei ausgeben!\n";
$h1 = new CIPP::InputHandle ("testdatei");
while ( $line = $h1->Read() ) {
print $line;
}
$h1 = undef;
print "\n\nSuchen:\n";
$h2 = new CIPP::InputHandle ("testdatei");
print "Status: ", $h2->Get_Init_Status(), "\n";
while ( $chunk = $h2->Read_Cond('"',1) ) {
print "GOT {$chunk}\n\n";
}
exit;
}
package CIPP::InputHandle;
$CIPP::InputHandle::obj_nr = 0;
$VERSION = "0.2";
sub new {
my $type = shift;
my ($input) = @_;
my $init_status = 1;
my $filehandle;
my $buffer;
$CIPP::InputHandle::obj_nr++;
if ( ref $input eq 'GLOB' or ref $input eq 'FileHandle' ) {
$filehandle = $input;
} elsif ( ref $input eq 'SCALAR' ) {
$filehandle = undef;
$buffer = $$input;
} elsif (not ref $input) {
$filehandle = "InputHandle".$CIPP::InputHandle::obj_nr;
open ($filehandle, $input) || ($init_status=0);
} else {
$filehandle = undef;
$init_status = 0;
}
$buffer = '' if !defined $buffer;
my $self = {
"filehandle" => $filehandle,
"buffer" => $buffer,
"init_status" => $init_status,
"comment_filter" => 0,
"line" => 0,
"obj_nr" => $CIPP::InputHandle::obj_nr
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
sub Read {
my $self = shift;
return undef if ! $self->{init_status};
my $result;
if ( $self->{buffer} ne '' ) {
$self->{buffer} =~ s/^([^\n]*)//;
$result = $1;
if ( $self->{buffer} =~ s/^\n// ) {
return "$result\n";
} else {
return $result;
}
}
if ( defined $self->{filehandle} ) {
my $filehandle = $self->{filehandle};
my $line;
if ( ! $self->{comment_filter} ) {
$line = scalar (<$filehandle>);
++$self->{line} if defined $line;
$line =~ s/\r//g;
return $line;
}
do {
$line = scalar (<$filehandle>);
++$self->{line} if defined $line;
$line =~ s/\r//g;
} while ( !eof($filehandle) && $line =~ /^\s*#/ );
if ( defined $line && $line =~ /^\s*#/ ) {
return undef;
} else {
return $line;
}
}
return undef;
}
sub Add_To_Buffer {
my $self = shift;
return undef if ! $self->{init_status};
my ($chunk) = @_;
$self->{buffer} = $chunk.$self->{buffer};
return 1;
}
sub Get_Init_Status {
my $self = shift;
return $self->{init_status};
}
sub Read_Cond {
my $self = shift;
return undef if ! $self->{init_status};
my ($magic, $with_escaping) = @_;	
my $buffer = '';
my ($line, $pos);
my $startpos = 0;
while ( $line = $self->Read() ) {
$buffer .= $line;
if ( -1 != ($pos = index ($buffer, $magic, $startpos)) ) {
if ( $with_escaping && $pos != 0 &&
substr($buffer,$pos-1,1) eq "\\" ) {
$startpos = $pos + length($magic);
} else {
$self->Add_To_Buffer
(substr $buffer, $pos+length($magic));
return substr ($buffer, 0, $pos+length($magic));
}
} else {
$startpos = length($buffer);
}
}
return $buffer;
}
sub Read_Cond_Quoted {
my $self = shift;
return undef if ! $self->{init_status};
my ($magic, $quote_char) = @_;
my $in_quotes = 0;
my $buffer = '';
my ($line, $sq, $sm);
my ($posq, $posm) = (-1,-1);
$line = $self->Read();
return '' if ! defined $line;
$buffer .= $line;
while ( 1 ) {
$sq = index ($buffer, $quote_char, $posq);
$sm = index ($buffer, $magic, $posm);
if ( $sm==-1 && $sq==-1 ) {
$line = $self->Read();
return $buffer if ! defined $line;
$buffer .= $line;
next;
}
if ( $sq > 0 && substr ($buffer, $sq - 1, 1) eq "\\" ) {
$posq = $sq + 1;
next;
}
if ( ($sm!=-1) && ($sm < $sq || $sq==-1) && ! $in_quotes ) {
$self->Add_To_Buffer
(substr $buffer, $sm+length($magic));
return substr $buffer, 0, $sm+length($magic);
}
if ( ($sm!=-1) && ($sm < $sq || $sq==-1) && $in_quotes ) {
$posm = $sm + 1;
next;
}
if ( ($sm!=-1) && ($sq < $sm || $sm==-1) ) {
$posq = $sq + 1;
$in_quotes = ($in_quotes ? 0 : 1);
next;
}
$line = $self->Read();
return $buffer if ! defined $line;
$buffer .= $line;
}
return $buffer;		# Achtung, da stand $result! noch nicht gecheckt!
}
sub Set_Comment_Filter {
my $self = shift;
return undef if ! $self->{init_status};
my ($comment_filter) = @_;
$self->{comment_filter} = $comment_filter;
}
sub Get_Line_Number {
my $self = shift;
return undef if ! $self->{init_status};
return $self->{line};
}
1;
__END__
=head1 NAME
CIPP::InputHandle - Input stream abstraction (file and memory I/O)
=head1 DESCRIPTION
This module abstracts from an input source. So it is possible to
read transparently from a file, filehandle or memory.
=head1 AUTHOR
Jörn Reder, joern@dimedis.de
=head1 COPYRIGHT
Copyright 1997-1999 dimedis GmbH, All Rights Reserved
This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself.
=head1 SEE ALSO
perl(1), CIPP (3pm)
