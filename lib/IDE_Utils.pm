package IDE_Utils;
sub Get_Timestamp {
my ($sec, $min, $hour, $mday, $mon, $year) = localtime(time);
++$mon;
$mon = "0".$mon if $mon < 10;
$mday = "0".$mday if $mday < 10;
$hour = "0".$hour if $hour <10;
$min = "0".$min if $min < 10;
$sec = "0".$sec if $sec < 10;
$year += ($year < 97 ) ? 2000 : 1900;
return "$year.$mon.$mday-$hour:$min:$sec";
}
sub Format_Timestamp {
my ($timestamp) = @_;
$timestamp =~ /^(\d+)\.(\d+)\.(\d+)-(\d+):(\d+):(\d+)$/;
return "$3.$2.$1-$4:$5:$6";
}
sub Object_Is_Dir_Locked {
my ($project, $object_path, $root_path) = @_;
my $path = $object_path;
$path =~ s![^/]+$!!;
my $found = 0;
while ( not $found ) {
my $file = "$path.locked";
if ( -e $file ) {
my $fh = new FileHandle;
open ($fh, $file ) or die "can't open $file";
my @projects = <$fh>;
close $fh;
my $prj;
foreach $prj (@projects) {
chop $prj;
if ( $prj eq $project ) {
$found = 1;
last;
}
}
}
last if $path eq "$root_path/";
$path =~ s![^/]+/$!! if not $found;
}
return if not $found;
$path =~ s!$root_path!!;
return $path;
}
1;
