package Project;
use Struct_File;
use IDE_Header;
use IDE_Utils;
use LkTyH;
use FileHandle;
use File::Path;
use File::Copy;
use Cwd;
use strict;
$Project::ERR_FOLDER_EXISTS = -1;
$Project::ERR_SYSTEM  = -2;
$Project::ERR_FOLDER_DOES_NOT_EXIST = -3;
$Project::ERR_OBJECT_EXISTS = -4;
$Project::ERR_OBJECT_DOES_NOT_EXIST = -5;
$Project::PROJECT_ALREADY_EXIST = -7;       # Projekt ist dem System bereits bekannt
$Project::UNKNOWN_PROJECT = -8;             # Projekt ist unbekannt
$Project::DIRECTORY_NOT_CREATED = -9;       # Verzeichnis konnte nicht angelegt werden
$Project::DIRECTORY_NOT_DELETED = -10;      # Verzeichnis konnte nicht geloescht werden
my $initial_version = "0.0.0.0";
sub new {
my ($type) = shift;
my ($project_file, $driver_file) = @_;
my $dfile = new Struct_File ($driver_file);
my $pfile = new Struct_File ($project_file);
my $init_status = $Struct_File::init_status;
my $href = $dfile->Get_List ("OBJECT_TYPES");
my ($driver, %object_types);
foreach $driver (keys %{$href}) {
my @ot_list = split ("\t", $href->{$driver});
my $ot;
foreach $ot (@ot_list) {
$object_types{$ot} = $driver;
}
}
my $object_ext = "|". join ("|", keys %object_types ) . "|";
my $self = {
"object_types" => \%object_types,
"object_ext" => $object_ext,
"project_file" => $pfile,
"driver_file" => $dfile,
"init_status" => $init_status
};
return bless $self, $type;
}
sub Tree_HTML {
my $self = shift;
my ($name, $open_folders, $object_sort, $spirit_cgi_url,
$driver_cgi_url, $icon_url, $ticket, $jump_folder) = @_;
$self->{name} = $name;
$self->{project_src} =
$self->{project_file}->Read ($name, "DIRECTORY")."/src";
$self->{open_folders} = $open_folders;
$self->{object_sort} = $object_sort;
my (@tree);
push @tree, $self->{name}."//";
$self->{open_folders}->{$self->{name}} = 1;
if ( defined $self->{open_folders}->{$self->{name}} ) {
$self->Read_Tree ("", \@tree);
}
my ($a) = ("align=top border=0");	# "width=18 height=18");
my ($item, $last_item, $i, $n, $depth);
$i = 0;
$n = scalar @tree - 1;
$depth = 0;
$last_item = undef;
my ($obj_icon, $pre_icon, $pre_href, $href,
$obj_type, $obj_dir, $driver, @pre_images, $obj_text);
foreach $item (@tree) {
if ( $item =~ /\/$/ ) {
my $check = $item;
$check =~ s/\/\/?$//;
$href="$spirit_cgi_url?event=edit_folder&dir=$check";
if ( $check eq $jump_folder ) {
print "<A NAME=jump>\n";
}
if ( defined $self->{open_folders}->{$check} ) {
$obj_icon = "icon_dir_open.gif";
$pre_href="$spirit_cgi_url?event=close&dir=$check";
$check =~ s/\/.*$//;
if ( $item !~ /\/\/$/ && $i != $n &&
($tree[$i+1] =~ /^$check/) ) {
$pre_icon="tree_minus_down.gif";
} else {
$pre_icon="tree_minus.gif";
}
} else {
$obj_icon = "icon_dir_closed.gif";
$pre_href="$spirit_cgi_url?event=open&dir=$check";
$check =~ s/\/.*$//;
if ( $item !~ /\/\/$/ && $i != $n &&
($tree[$i+1] =~ /^$check/) ) {
$pre_icon="tree_plus_down.gif";
} else {
$pre_icon="tree_plus.gif";
}
}
} else {
($obj_type) = ( $item =~ /^.*\.(.*)$/ );
$driver = $self->{object_types}->{$obj_type};
my $object = $item;
$object =~ s/\.[^\.]*$//;
$object =~ s!/!.!g;
$href="$driver_cgi_url/$driver/driver.cgi?".
"event=edit&object_type=$obj_type&object=$object";
$obj_icon = "icon_$obj_type.gif";
($obj_dir) = ( $item =~ /^(.*)\// );
if ( $i != $n &&
$tree[$i+1] =~ /^$obj_dir\// ) {
$pre_icon="tree_rline.gif";
} else {
$pre_icon="tree_eline.gif";
}
$pre_href = "";
}
$obj_text = $item;
$obj_text =~ s/\/\/?$//;
$obj_text =~ /\/?([^\/]+)$/;
$obj_text = $1;
($obj_text) = $obj_text =~ /^([^\.]+)/;
my $test_dirs = $item;
$test_dirs =~ s/\/\/$/\//;
$test_dirs =~ s/[^\/]+//g;
$depth = length($test_dirs);
if ( length($test_dirs) <= scalar (@pre_images) ) {
if ( $item =~ /\/$/ ) {
splice @pre_images, $depth-1;
} else {
splice @pre_images, $depth;
}
}
my ($p, $first_skipped);
foreach $p (@pre_images) {
print "<img src=$icon_url/$p $a>" if ($first_skipped);
$first_skipped = 1;
}
$pre_href .= "&ticket=$ticket&project=$name" if $pre_href ne "";
$href .= "&ticket=$ticket&project=$name";
if ($i) {
$pre_href .= "#jump" if $pre_href ne '';
print "<a href=$pre_href>" if $pre_href ne '';
print "<img src=$icon_url/$pre_icon $a>";
print "</a>" if $pre_href ne "";
}
print "<a href=$href target=ACTION><img src=$icon_url/$obj_icon $a>";
print "&nbsp;$obj_text</a><br>\n";
if ( $item =~ /\/\/$/ ) {
push @pre_images, "tree_empty.gif"
} elsif ( $item =~ /\/$/ ) {
push @pre_images, "tree_vline.gif";
}
++$i;
}
print "\n";
$self->{open_folders} = undef;
$self->{object_sort} = undef;
return;
}
sub Read_Tree {
my $self = shift;
my ($dir, $tree) = @_;
my $fullpath = $self->{project_src}."/".$dir;
my $project_name = $self->{name};
my (@dir, %obj, $entry, $ext);
opendir (DIR, "$fullpath") or die "opendir $fullpath";
my $objects_in_dir = 0;
while (defined ($entry = readdir (DIR)) ) {
next if $entry =~ /^\./;
next if $entry eq 'CVS';
($ext) = $entry =~ /.*\.(.*)$/;
next if -f $entry &&
-1 == index ($self->{object_ext}, "|".$ext."|");
push @dir, "$dir/$entry" if -d "$fullpath/$entry";
if ( -f "$fullpath/$entry" ) {
push @{$obj{$ext}}, "$dir/$entry";
$objects_in_dir = 1;
}
}		
closedir DIR;
my (@sort_dir);
@sort_dir = sort @dir;
my ($d);
foreach $d (@sort_dir) {
if ( $d eq $sort_dir[scalar @sort_dir - 1] &&
! $objects_in_dir ) {
push @{$tree}, "${project_name}$d//";	# dann ein / mehr hinten dran
} else {
push @{$tree}, "${project_name}$d/";	# nur ein / am Ende
}
if ( defined $self->{open_folders}->{$project_name.$d} ) {
$self->Read_Tree ($d, $tree);
}
}
my ($ot, $object);
foreach $ot (@{$self->{object_sort}}) {
if ( defined $obj{$ot} ) {
foreach $object (sort(@{$obj{$ot}})) {
push @{$tree}, $project_name.$object;
}
}
}
return 1;
}
sub Get_Project_Dir {
my $self = shift;
my ($project) = @_;
return $self->{project_file}->Read ($project, "DIRECTORY");
}
sub Get_Object_Path {
my $self = shift;
my ($object) = @_;
my ($project) = $object =~ /^([^\.]+)/;
return undef if $project eq '';
$object =~ s/^([^\.]+)\.?//;
$object =~ s!\.!/!g;
my $project_dir = $self->{project_file}->Read ($project, "DIRECTORY");
return undef if ! defined $project_dir;
return "$project_dir/src/$object";
}
sub Add_Folder {
my $self = shift;
my ($project, $reldir, $name) = @_;
if ( ! $self->Object_Name_OK ($name) ) {
return "Der Ordnername ist ung�ltig";
}
my $folder = "$reldir/$name";
my $object_name = $folder;
$object_name =~ s!/!\.!g;
if ( ! $self->Object_Name_Unique ($object_name) ) {
return "Es gibt ein Objekt oder einen Ordner mit diesem Namen";
}
my $project_dir = $self->{project_file}->Read ($project, "DIRECTORY");
$folder =~ s/^$project\///;
my $newdir = "$project_dir/src/$folder";
if ( ! mkdir ($newdir, 0775 ) ) {
return "Es ist ein Systemfehler aufgetreten!";
} else {
return undef;
}
}
sub Del_Folder {
my $self = shift;
my ($project, $folder) = @_;
my $project_dir = $self->{project_file}->Read ($project, "DIRECTORY");
$folder =~ s/^$project\///;
my $deldir = "$project_dir/src/$folder";
if ( ! -d $deldir ) {
return $Project::ERR_FOLDER_DOES_NOT_EXIST;
} 
if ( rmtree ($deldir) <= 0 ) {
return $Project::ERR_SYSTEM;
} else {
return 1;
}
}
sub Add_Object {
my $self = shift;
my ($project, $reldir, $name, $object_type, $object_desc,
$username) = @_;
if ( ! $self->Object_Name_OK ($name) ) {
return "Der Objektname ist ung�ltig";
}
my $relpath = "$reldir/$name";
my $object_name = $relpath;
$object_name =~ s!/!.!g;
if ( ! $self->Object_Name_Unique ($object_name) ) {
return "Ein Objekt oder Ordner mit diesem Namen gibt es bereits";
}
my ($driver, $type) = split (":", $object_type, 2);
my $project_dir = $self->{project_file}->Read ($project, "DIRECTORY");
my $project_copyright = $self->{project_file}->Read ($project, "COPYRIGHT");
$relpath =~ s/^$project\///;
my $new_object = "$project_dir/src/$relpath.$type";
my $driver_tags = $self->{driver_file}->Read ($driver, "HEADER_TAGS");
my $header = new IDE_Header (undef, $driver_tags);
$header->Put_Tag ("OBJECT_VERSION", $initial_version);
$header->Put_Tag ("OBJECT_NAME", $object_name);
$header->Put_Tag ("OBJECT_TYPE", $type);
$header->Put_Tag ("DESCRIPTION", $object_desc);
$header->Put_Tag ("COPYRIGHT", $project_copyright );
$header->Put_Tag ("MODIFICATION_HISTORY", "frisch angelegt");
$header->Put_Tag ("LAST_MODIFY_BY", $username);
$header->Put_Tag ("LAST_MODIFY_DATE", IDE_Utils::Get_Timestamp());
my $tag;
foreach $tag ( split (/[\t\n]/, $driver_tags ) ) {
$header->Put_Tag ($tag, "");
}
open (OBJECT, "> $new_object") || return $Project::ERR_SYSTEM;
if ( $header->Write_IDE_Header ( \*OBJECT ) < 0 ) {
close (OBJECT);
unlink ($new_object);
return "Es ist ein Systemfehler aufgetreten";
}
close (OBJECT);
if ( $IDE::cvs ) {
my $new_object_file = "$project_dir/src/$reldir/.new_$name.$type";
$new_object_file =~ s!src/$project!src!;
open (NEW, "> $new_object_file") or die "can't write $new_object_file";
print NEW "buh!\n";
close (NEW);
}
return undef;
}
sub Del_Object {
my $self = shift;
my ($project, $object_name, $object_type) = @_;
my $project_dir = $self->{project_file}->Read ($project, "DIRECTORY");
$object_name =~ s/^$project\.//;
$object_name =~ s!\.!/!g;
my $object_path = "$project_dir/src/$object_name.$object_type";
my $deldir = "$project_dir/src/$object_name.$object_type";
$deldir =~ s!([^/]+)$!.$1!;
if ( (-d $deldir) and (rmtree ($deldir) <= 0) ) {
return $Project::ERR_SYSTEM;
}
return unlink ($object_path) - 1;
}
sub Get_List {
my $self = shift;
my ($fieldname) =shift;        # Uebergabeparameter
return $self->{project_file}->Get_List($fieldname);
}
sub Create {
my $self = shift;
my ($project, 
$directory, 
$description,
$used_drivers, 
$creator, 
$copyright) = @_;           # Uebergabeparameter
unless ( defined $self->{project_file}->Read( $project, "DIRECTORY")) { 
my $um = umask 000;
eval { 
mkpath( ["$directory",
"$directory/src",
"$directory/prod"] , 0, 0770);
};
return $Project::DIRECTORY_NOT_CREATED if $@;
umask $um;
$self->{project_file}->Write( $project, "DIRECTORY", $directory);
$self->{project_file}->Write( $project, "DESCRIPTION", $description);
$self->{project_file}->Write( $project, "USED_DRIVERS", $used_drivers);
$self->{project_file}->Write( $project, "CREATOR", $creator);
$self->{project_file}->Write( $project, "COPYRIGHT", $copyright);
my $passwd_obj = new Passwd( $IDE::Passwd_File);
my ($flag_str, $project_str);
$passwd_obj->Get_User( $creator, \$flag_str, \$project_str);
$project_str .= ",$project";
$passwd_obj->Modify_User( $creator, '', $flag_str, $project_str);
}
else {
return $Project::PROJECT_ALREADY_EXIST;
}
1;
}
sub Delete { 
my $self = shift;
my ($project) = shift;           # Uebergabeparameter
my $directory = $self->{project_file}->Read( $project, "DIRECTORY");
if ( defined $directory) {
$self->{project_file}->Delete( $project);
my $passwd_obj = new Passwd( $IDE::Passwd_File);
my $user_hash_ref = $passwd_obj->Get_Userlist('USER');
my @user_list = keys %{$user_hash_ref};
my $user;
foreach $user ( @user_list) {
if ( $passwd_obj->Check_Project_Access( $user, $project) == 1 ) {
my ( $flags, $project_list);
$passwd_obj->Get_User( $user, \$flags, \$project_list);
$project_list =~ s/(,?)$project(,?)/$1$2/;
$project_list =~ s/^,|,$//;
$passwd_obj->Modify_User( $user, "",$flags, $project_list);
}
}
my $current_dir = cwd();          # aktuelles Verzeichnis sichern	
my $fh = new FileHandle;          # Session-Verzeichnis
my @ticket_list;                  # Liste aller .dir Dateien im Verzeichnis
chdir($IDE::Session_Dir);
opendir $fh, "." or 
die "Verzeichnis $IDE::Session_Dir konnte nicht geoeffnet werden $!\n";
@ticket_list = grep /\.dir$/, readdir $fh;
closedir $fh;
my $ticket;
foreach $ticket ( @ticket_list) {
$ticket =~ s/.dir$//;
my $prj_folders = new LkTyH ($IDE::Session_Dir.$ticket);	
my @dir_list = grep /^$project/, keys(%{$prj_folders->{LkTyH_hash}});
my $dir;
foreach $dir ( @dir_list) {
delete $prj_folders->{LkTyH_hash}->{$dir};
}
$prj_folders = undef;
}
chdir($current_dir);
eval {
rmtree( $directory, 0, 0);
};
return $Project::DIRECTORY_NOT_DELETED if $@;
}
else {
return $Project::UNKNOWN_PROJECT;
}
1;
}
sub Get_Objects_In_Folder {
my $self = shift;
my ($folder, $object_type) = @_;
$object_type ||= '';
my %object_hash;
my $dh = new FileHandle;
my @stack;
my $folder_dir = $self->Get_Object_Path ($folder);
$folder =~ /([^\.]*)/;
my $project = $1;
my $project_src = $self->{project_file}->Read ($project, "DIRECTORY")."/src";
push @stack, $folder_dir;
my $dir;
while ( $dir = pop @stack ) {
opendir $dh, $dir or 
die ("Verzeichnis $dir konnte nicht geoeffnet werden");
my @files = grep !/^\./, readdir $dh;
closedir $dh;
my ($file, $driver, $object);
foreach $file (@files) {
if ( -d "$dir/$file" ) {
push @stack, "$dir/$file";
next;
}
$file =~ /\.(.*)$/;
$driver = $self->{object_types}->{$1};
$object = "$dir/$file";
$object =~ s!^$project_src/+!!;        # Projekt-Verz rauspopeln
$object =~ s!/!.!g;                    # Slashes in Punkte verwandeln
$object =~ s!\.([^\.]+)$!\t$1!;        # Dateiendung wird mit TAB getrennt
if ( $object_type eq '' || $1 eq $object_type ) {
push @{$object_hash{$driver}}, "$project.$object";
}
}
}
return \%object_hash;
}
sub Object_Name_OK {
my ($self, $check_name) = @_;
return 1 if $check_name =~ /^[\w-]+$/;
return undef;
}
sub Object_Name_Unique {
my ($self, $object) = @_;
my $path = $self->Get_Object_Path ($object);
return undef if -d $path;
if (<$path.*>) {
return undef
}
return 1;
}
sub bin2asc {
my ($text, $rx) = @_;
my $x = $$rx;
print STDERR "$text: ";
my $u;
for ($u=0; $u<length($x); ++$u) {
printf STDERR "%3d ", ord(substr($x,$u,1));
}
print STDERR "\n";
}
1;
