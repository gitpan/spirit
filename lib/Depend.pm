package Depend;
use File::Find;
use LKDB;
use strict;
sub new {
my ($type) = shift;
my ($project, $class, $project_dir) = @_;
$project_dir =~ s!/$!!;
my $init_status = 1;
my $self = {
"project"  => $project,
"class" => $class,
"project_dir" => $project_dir,
"init_status" => $init_status
};
return bless $self, $type;
}
sub depends_on_file {
my $self = shift;
my ($object) = @_;
$object =~ s/^[^\.]+//;	# Projektanteil rausschneiden
$object =~ s!\.!/!g;	# alle . zu / machen
$object =~ s!:!\.!;	# : von Objekttyp-Trennung zu .extension machen
$object =~ s!([^/]+)$!\.$1!;	# . vor Objektnamen setzen
my $meta_dir = $self->{project_dir}.$object;
mkdir $meta_dir, 0775 if not -d $meta_dir;
return "$meta_dir/.depends_on";
}
sub dependants_file {
my $self = shift;
my ($object) = @_;
$object =~ s/^[^\.]+//;	# Projektanteil rausschneiden
$object =~ s!\.!/!g;	# alle . zu / machen
$object =~ s!:!\.!;	# : von Objekttyp-Trennung zu .extension machen
$object =~ s!([^/]+)$!\.\1!;	# . vor Objektnamen setzen
my $meta_dir = $self->{project_dir}.$object;
mkdir $meta_dir, 0775 if not -d $meta_dir;
return "$meta_dir/.dependants";
}
sub Put_Depends_On {
my $self = shift;
my ($object, $depends_on) = @_;
my $project = $self->{project};
my $class = $self->{class};
my $file = $self->depends_on_file ($object);
my @ary = keys %{$depends_on};
my $record = join (
"\t", 
map { my $x = $_; $x =~ s/^[^\.]+//; $_ = $x } @ary
);
my $lkdb = new LKDB ($file, "ex");
if ( $record ne '' ) {
$lkdb->{hash}->{"$project:$class"} = $record;
} else {
delete $lkdb->{hash}->{"$project:$class"};
}
$lkdb = undef;
1;
}
sub Get_Depends_On {
my $self = shift;
my ($object) = @_;
my $project = $self->{project};
my $class = $self->{class};
my $file = $self->depends_on_file ($object);	
my $lkdb = new LKDB ($file, "ex");
my (%hash, @hash);
my @ary = split ("\t", $lkdb->{hash}->{"$project:$class"});
@hash{@ary} = (1) x ( map { my $x = $_; $x =~ s/^\./$project\./; $_ = $x } @ary );
$lkdb = undef;
return \%hash;
}
sub Put_Depending_Objects {
my $self = shift;
my ($object, $dependants) = @_;
my $project = $self->{project};
my $class = $self->{class};
my $file = $self->dependants_file ($object);	
my @ary = keys %{$dependants};
my $record = join (
"\t", 
( map { my $x = $_; $x =~ s/^[^\.]+//; $_ = $x } @ary )
);
my $lkdb = new LKDB ($file, "ex");
if ( $record ne '' ) {
$lkdb->{hash}->{"$project:$class"} = $record;
} else {
delete $lkdb->{hash}->{"$project:$class"};
}
$lkdb = undef;
1;
}
sub Get_Depending_Objects {
my $self = shift;
my ($object, $all_projects) = @_;
my $project = $self->{project};
my $class = $self->{class};
my $file = $self->dependants_file ($object);	
my $lkdb = new LKDB ($file, "ex");
my (%hash, @hash);
my @ary;
if ( not $all_projects ) {
@ary = map { "$project$_" } split ("\t", $lkdb->{hash}->{"$project:$class"});
} else {
my ($k, $v);
while ( ($k, $v) = each %{$lkdb->{hash}} ) {
next if $k !~ /([^:]+):$class/;
push @ary, map { "$1$_" } split ("\t", $v);
}
}
$lkdb = undef;
if ( @ary ) {
@hash{@ary} = (1) x @ary;
return \%hash;
}
return;
}
sub Modify_Dependencies {
my $self = shift;
my ($object, $depends_on_orig) = @_;
if ( ! defined $depends_on_orig ) {
$depends_on_orig = {};
}
my $project = $self->{project};
$object =~ s/^[^\.]+/$project/;
my $depends_on;
my ($k);
foreach $k ( keys %{$depends_on_orig} ) {
$k =~ s/^[^\.]+/$project/;
$depends_on->{$k} = 1;
}
my $old_depends_on = $self->Get_Depends_On ($object);
my $o;
foreach $o ( keys %{$old_depends_on} ) {
if ( ! defined $depends_on->{$o} ) {
my $do = $self->Get_Depending_Objects ($o);
delete $do->{$object};
$self->Put_Depending_Objects ($o, $do);
}
}
foreach $o ( keys %{$depends_on} ) {
if ( ! defined $old_depends_on->{$o} ) {
my $do = $self->Get_Depending_Objects ($o);
$do->{$object} = 1;
$self->Put_Depending_Objects ($o, $do);
}
}
$self->Put_Depends_On ($object, $depends_on);
return;
}
sub Delete_Object {
my $self = shift;
my ($object) = @_;
my $depends_on = $self->Get_Depends_On ($object);
my $o;
foreach $o (keys %{$depends_on} ) {
my $do = $self->Get_Depending_Objects ($o);
delete $do->{$object};
$self->Put_Depending_Objects ($o, $do);
}
$self->Put_Depends_On ($object, {});
}
sub Clear_Dependencies {
my $self = shift;
my ($class) = @_;
$Depend::clear_class = "$self->{project}:$self->{class}";	# für find
find (\&clear_one_dependency, $self->{project_dir});
}
sub clear_one_dependency {
return if not /.depends_on$/ and not /.dependants$/;
$Depend::{"$File::Find::dir/$_"} = 1;
my $lkdb = new LKDB ($_, "ex") or die "\ncan't open db file $_";
my @del_list;
my ($k, $v);
while ( ($k, $v) = each ( %{$lkdb->{hash}} ) ) {
push @del_list, $k if $k =~ /^$Depend::clear_class/;
}
my $o;
foreach $o ( @del_list ) {
delete $lkdb->{hash}->{$o};
}
}
1;
