#==============================================================================
#
# SYNOPSIS
#	spirit-install.pl
#
# REVISION
#	$Id: spirit-install.pl,v 1.1.1.1 1999/06/25 10:14:54 joern Exp $
#
# BESCHREIBUNG
#	Installiert spirit auf einem Unix- oder Windows NT System
#
#==============================================================================
#
# COPYRIGHT
#	(c) 1997 dimedis GmbH, All Rights Reserved
#
#------------------------------------------------------------------------------
#
# MODIFICATION HISTORY
#	05.01.98 0.1.0.0 joern
#		Erste Version mit folgenden Funktionen:
#		- Pruefen, ob als richtiger User/Group aufgerufen
#		- Checken ob alle benoetigten Perl-Module installiert sind
#		- ide.cnf initialisieren, Abfrage von Parametern:
#		  + URL fuer ./cgi-bin
#		  + URL fuer ./spirit-icons
#		- ./htdocs/index.html patchen
#		- symb. Links auf ide.cnf verteilen
#		- Filemodes korrekt setzen
#		- etc/drivers initialisieren
#		- etc/passwd initialisieren
#
#	07.01.98 0.1.0.1 joern
#		Erweiterungen:
#		- Check auf Perl 5.004
#		- Perl-Interpreter-Pfad reinpatchen
#		- Config-Eintraege fuer spirit-User generieren
#
#	20.01.98 0.1.0.2 joern
#		- Bug entfernt: Patch_Perl_Bin_Path()
#		  Wenn spirit-install ein weiteres Mal aufgerufen wurde, sind
#		  die Benutzer-Voreinstellungen wertlos geworden, weil die
#		  erste Zeile mit #!/usr/local/bin/perl ueberschrieben wurde.
#		  Dort stand aber 'package USER;' :)
#
#	13.03.98 0.1.0.3 joern
#		- Versionsnummer wird nun auch aus ide.cnf geholt
#		- Check auf Perl-Module DB_File
#
#	06.04.98 0.1.0.4 joern
#		- Lizenz abfragen, wenn noch nicht vorhanden
#
#	14.05.98 0.1.0.5 joern
#		- in @Cfg::Delete stehen zu löschende Files (im Falle eines
#		  Updates). Diese Dateien werden einfach gelöscht, falls sie
#		  existieren.
#
#	30.09.98 0.1.0.6 joern
#		- Bugfix: beim Installieren von CIPP_Runtime.pm wurden je nach
#		  umask die Rechte des prod/cgi-bin Verzeichnisses verunstaltet
#
#	26.01.99 0.1.0.7 joern
#		- Wegen Umstellung CIPP_Runtime -> CIPP::Runtime mußte das
#		  Update der Library entsprechend angepaßt werden.
#		- Abfrage der Lizenz rausgenommen
#
#	26.02.99 0.18 joern
#		- Initialisierungsfragen haben nun als Default Ausgabe [n]
#
#	16.03.99 0.19 joern
#		- Ausgabe der Lizenztexte, Installation nur nach
#		  Bestätigung
#		- Copyright auf 1999 erweitert
#
#	19.05.1999 joern
#		- Anpassungen für Windows NT
#
#==============================================================================

BEGIN { unshift (@INC, "lib"); }

use strict;
use Cwd;
use Struct_File;
use Passwd;
use Project;
use Configure;
use Config;
use File::Path;
use File::Find;
use File::Copy;

$main::IN_SPIRIT_INSTALL = 1;
require "admin/install.conf";

if ( -f "etc/ide.cnf" ) {
	# etc/ide.cnf existiert bereits => Update,
	# für korrekte Defaultwerte
	require "etc/ide.cnf";
} else {
	# sonst admin/ide.cnf holen: die ORIGINALE der Distribution
	require "admin/ide.cnf";
}

my $opt = shift @ARGV;

$| = 1;

if ( $opt eq 'etc-only' ) {
	Patch_Perl_Bin_Path ();
        Init_Drivers();
        Init_Passwd();
        Init_Config();
        exit;
}

Header ();
Check_Installation_User ();
#License ();
Info ();
Wait();
Check_Perl_Version ();
Check_Modules ();
my $htdocs_url = Gen_IdeDotConf ();
Patch_Perl_Bin_Path ();
Init_Drivers ();
Init_Passwd ();
Init_Config ();
Replace_Runtime_Modules ();
Delete_Files ();
Set_Filemodes ();

Print_Success_Message ($htdocs_url);

exit;

# Subroutinen -----------------------------------------------------------------

sub Header {
	print "\n" x 5;
	print "spirit - Erfolg ist programmierbar                   ";
	print "(c) 1997-1999 dimedis GmbH\n";
	print "-" x 79, "\n";
	print "\nInstallation von spirit Version $IDE::Package_Version\n\n";
}

sub License {
	print <<__EOT;
Hinweise zur Lizenzvereinbarung
===============================

Bevor Sie spirit nutzen können, müssen Sie einen Lizenzvertrag
abschließen, indem Sie sich einen der folgenden Lizenztexte durchlesen und
anschließend bestätigen, daß Sie diesem zustimmen. Die Installation wird
nur in diesem Falle fortgesetzt.

Es gibt drei Lizenzmodelle für die Verwendung von spirit.

1. private Nutzung (kostenlos)
2. kommerzielle Testnutzung (befristet kostenlos)
3. kommerzielle Nutzung (kostenpflichtig)

Wählen Sie bitte das Lizenzmodell aus, unter dem Sie spirit benutzen
möchten. Daraufhin wird ihnen der Vertragstext zum Lesen angezeigt.
Anschließend müssen Sie bestätigen, daß Sie die Lizenz anerkennen und
demnach berechtigt sind, spirit zu nutzen.

Andernfalls wird die Installation an dieser Stelle abgebrochen.

__EOT
	my $license;
	do {
		print "Wählen Sie das Lizenzmodell (1..3, A=Abbruch) : ";
		chomp($license = <STDIN>);
		print "license='$license'\n";
		$license =~ tr/A-Z/a-z/;
		print "license='$license'\n";
	} while ( $license !~ /^[123a]$/ );

	if ( $license eq 'a' ) {
		print "\nDie Installation wird abgebrochen!\n\n";
		exit;
	}

	my %licenses = ( 1 => "PRIVATE", 2 => "TEST", 3 => "COMMERCIAL" );
	$license = $licenses{$license};
	print "\n\n";

	system ("$Config{pager} license/LICENSE.$license");

	print "\n";
	Wait();
	
	print <<__EOT;

Nun müssen Sie bestätigen, daß Sie den Lizenzvertrag anerkennen und
somit berechtigt sind, spirit zu nutzen. Bitte geben Sie in diesem
Fall "Ja" ein. Wenn Sie den Lizenzvertrag nicht anerkennen, so
beantworten Sie die Frage mit "Nein" und die Installation wird an
dieser Stelle abgebrochen!

__EOT
	my $answer;
	do {
		print "Erkennen Sie den Lizenzvertrag an? (Ja/Nein) : ";
		chomp ($answer = <STDIN>);
		$answer =~ tr/A-Z/a-z/;
	} while ( $answer ne "ja" and $answer ne "nein" );

	if ( $answer eq "nein" ) {
		print "\nDie Installation wird abgebrochen!\n\n";
		exit;
	}
}

sub Info {
	print <<_EOL

Bitte beachten Sie die Lizenzvereinbarungen im Ordner license/
der spirit Installation. spirit steht unter denselben Lizenzmodellen
wir Perl, also wahlweise unter Artistic oder GNU Public License.


Bei der Installation wird folgendes durchgefuehrt:
==================================================
  - Es wird ueberprueft, ob die Systemvorausetzungen erfuellt sind.
  - Dann werden von Ihnen die Mappings ihres Webservers abgefragt.
  - Einige Konfigurationsdateien werden initialisiert.
  - Die Dateirechte aller spirit-Dateien werden korrekt gesetzt, dabei wird
    auch geprueft, ob alle benoetigten Dateien vorhanden sind.

_EOL
}

sub Check_Installation_User {
	return if $IDE::OS;		# nur unter Unix

	my $pw_uid = getpwnam ($Cfg::Check_User);
	my $pw_gid = getgrnam ($Cfg::Check_Group);

	if ( $pw_uid != $< or $pw_gid != $( ) {
		print <<_EOL;
Bitte melden Sie sich als folgender Benutzer am System an, bevor Sie dieses
Installationsprogramm ausfuehren:

Benutzer:  $Cfg::Check_User
Gruppe:    $Cfg::Check_Group

_EOL
		exit;
	}
}

sub Check_Perl_Version {
	print "=> Pruefe Perl-Version... ";
	eval "require $Cfg::Perl_Version; ";
	if ( $@ ) {
		print "Fehler!\n";
		$@ =~ /version\s+([\d\.]+)/;
		Fatal ("Es wird Perl $Cfg::Perl_Version benoetigt, ".
		       "Sie haben nur Version $1.");
	} else {
		print "Ok\n";
	}
}

sub Check_Modules {
	my ($error, $warning, $module, $type);

	print "=> Checke die Perl-Installation... ";

	while ( ($module, $type) = each %Cfg::Check_Modules ) {
		eval "use $module;";
		$warning .= "\t- $module\n" if $@ and $type eq "optional";
		$error   .= "\t- $module\n" if $@ and $type eq "required";
	}

	if ( defined $warning ) {
		print "Warnung!\n\nFolgende Perl-Module sind ";
		print "nicht vorhanden, die u.U. benötigt werden:\n";
		print $warning;
		print "\nEs kann weiter installiert werden, wenn Sie trotzdem ";
		print "abbrechen moechten,\ndruecken Sie bitte Ctrl+C\n";
		print "\n=> Checke die Perl-Installation... ";
	}

	if ( defined $error ) {
		print "Fehler!\n\nDie folgenden Perl-Module muessen ";
		print "installiert sein:\n";
		print $error;
		print "\nDie Installation wird abgebrochen\n\n";
		exit;
	}

	print "Ok\n" if ! defined $error;
}

sub Gen_IdeDotConf {
	my $cdir = cwd();
	my ($htdocs_url, $cgi_url);

	print "\n";
	print "Bitte geben Sie an, wie das Dokument-Mapping ihres Webservers ";
	print "auf das folgende\nVerzeichnis lautet ";
	print "(Drücken Sie Enter für: $IDE::Htdocs_Url)\n\n";
	print "$cdir/htdocs -> ";
	chomp($htdocs_url = <STDIN>);
	$htdocs_url =~ s/\s+$//;

	$htdocs_url = $IDE::Htdocs_Url if $htdocs_url eq "";
	$htdocs_url .= "/" if $htdocs_url !~ /\/$/;
	$htdocs_url = '/'.$htdocs_url if $htdocs_url !~ /^\//;
	print "\n";
	print "=> Eingestelltes Dokumenten-Mapping: '", $htdocs_url, "'\n";
	print "\n";

	print "Bitte geben Sie an, wie das CGI-Mapping ihres Webservers ";
	print "auf das folgende\nVerzeichnis lautet ";
	print "(Drücken Sie Enter für: $IDE::Cgi_Url)\n\n";
	print "$cdir/cgi-bin -> ";
	chomp($cgi_url = <STDIN>);
	$cgi_url =~ s/\s+$//;

	$cgi_url = $IDE::Cgi_Url if $cgi_url eq "";
	$cgi_url = '/'.$cgi_url if $cgi_url !~ /^\//;
	$cgi_url =~ s!/$!!;
	print "\n";
	print "=> Eingestelltes CGI-Mapping: '", $cgi_url, "'\n";
	print "\n";

	print "=> Erstelle Konfigurationsdatei... ";

	if ( ! open (CNF, "./admin/ide.cnf") ) {
		print "Fehler!\n";
		Fatal ("Konnte ./admin/ide.cnf nicht oeffnen!");
	}

	if ( ! open (TMP, "> $IDE::OS_temp_dir/ide.cnf") ) {
		print "Fehler!\n";
		Fatal ("Konnte $IDE::OS_temp_dir/ide.cnf nicht oeffnen!");
	}

	my $main_dir_patched = 0;
	while (<CNF>) {
		s/^\$Cgi_Url.*/\$Cgi_Url = "$cgi_url";/;
		s/^\$Htdocs_Url.*/\$Htdocs_Url = "$htdocs_url";/;
		if ( ! $main_dir_patched ) {
			s/^(\s*)\$Main_Directory.*/$1\$Main_Directory = "$cdir\/";/
				and $main_dir_patched = 1;
		}
		print TMP;
	}

	close (CNF);
	close (TMP);

	if ( not move ("$IDE::OS_temp_dir/ide.cnf", "./etc/ide.cnf") ) {
		print "Fehler!\n";
		Fatal ( "Konfigurationsdatei konnte nicht erstellt werden!\n" );
	}

	print "Ok\n";

	# patche htdocs/index.html

	print "=> Erstelle htdocs/index.html... ";

	if ( ! open (INDEX, "./htdocs/index.html") ) {
		print "Fehler!\n";
		Fatal ("Konnte ./htdocs/index.html nicht oeffnen!");
	}

	if ( ! open (TMP, "> $IDE::OS_temp_dir/index.html") ) {
		print "Fehler!\n";
		Fatal ("Konnte $IDE::OS_temp_dir/index.html nicht oeffnen!");
	}

	while (<INDEX>) {
		s!<FRAME NAME.*!<FRAME NAME="spirit" SRC="$cgi_url/ide.cgi">!;
		print TMP;
	}

	close (INDEX);
	close (TMP);

	if ( not move("$IDE::OS_temp_dir/index.html", "./htdocs/index.html" ) ) {
		print "Fehler!\n";
		Fatal ( "htdocs/index.html konnte nicht erstellt werden!\n" );
	}

	print "Ok\n";

	return $htdocs_url;
}

sub Patch_Perl_Bin_Path {
	print "=> Patche Scripts mit dem Pfad des Perl-Interpreters... ";

	find ( \&Patch_Perl_Bin_Path_In_File, "." );

	print "Ok\n";
}

sub Patch_Perl_Bin_Path_In_File {
	return if ! /\.pl$/ and ! /\.cgi/;
	return if -l;	# sonst ist der Symlink nacher weg (durch umkopieren)
	return if $File::Find::dir =~ /user-config$/;

	my $file = $_;

	if ( ! open (PERL, $file) ) {
		print "Fehler!\n";
		Fatal ("Konnte $file nicht oeffnen!");
	}
	if ( ! open (PATCH, "> $IDE::OS_temp_dir/sp$$") ) {
		print "Fehler!\n";
		Fatal ("Konnte $IDE::OS_temp_dir/sp$$ nicht oeffnen!");
	}

	my $patched;
	my $first_line = <PERL>;
	if ( $first_line =~ /^#!/ ) {
		print PATCH "#!",$Config{perlpath},"\n";
		$patched = 1;
	} else {
		print PATCH $first_line;
	}

	while (<PERL>) {
		print PATCH;
	}

	close (PERL);
	close (PATCH);

	if ($patched) {
		if ( not move ("$IDE::OS_temp_dir/sp$$", "$file") ) {
			print "Fehler!\n";
			Fatal ("Fehler beim Patchen! (mv $IDE::OS_temp_dir/sp$$ $file) $!\n");
		}
	} else {
		unlink "$IDE::OS_temp_dir/sp$$";
	}
}

sub Set_IdeDotConf_SymLinks {
	my $cdir = cwd();
	my ($dir, $relpath);

	print "=> Setze symbolische Links auf Konfigurationsdateien... ";

	foreach $dir (@Cfg::IdeDotConf_SymLinks) {
		my ($tmp, $cnt, $relpath);
		$tmp = $dir; $cnt = 1;
		$tmp =~ s!/!$cnt++!eg;
		$relpath = "../" x $cnt;
		my $command =	"rm -f $cdir/$dir/ide.cnf;".
				"ln -s ${relpath}etc/ide.cnf $cdir/$dir";
		my $error = `$command 2>&1`;

		if ( $error ne '' ) {
			print "Fehler!\n";
			Fatal ("Symbolischer Link konnten nicht gesetzt werden!".
			       "\n".$error);
		}
	}
	print "Ok\n";
}


sub Delete_Files {
	my $file;

	foreach $file (@Cfg::Delete) {
		unlink "./$file" if -e $file;
	}
}


sub Set_Filemodes {
	my ($lref, $commands);
	
	return if $IDE::OS;	# nur bei Unix
	
	print "=> Setze Dateirechte... ";

	umask 0000;

	my @errors;
	foreach $lref (@Cfg::File_Modes) {
		my $files = $lref->[0];
		my @tmp = eval ("<$files>");
		my @files = grep (!/CVS/, @tmp);
		chmod oct($lref->[1]), @files or
			push @errors, "chmod $lref->[1] $files: $!";
	}

	if ( @errors ) {
		print "\n\n";
		print "Warnung: bei folgenden Dateien sind Fehler aufgetreten:\n";
		print join ("\n",@errors), "\n\n";
	} else {
		print "Ok\n\n";
	}
}

sub Replace_Runtime_Modules {
	print "=> Prüfe auf vorhandene Projekte... ";

	my $ph = new Project ($IDE::Project_File, $IDE::Driver_File);
	if ( $ph->{init_status} != 1 ) {
		print "Fehler\n";
		Fatal ("Fehler beim Einlesen der Projektinformationen");
	}

	my $href = $ph->Get_List ('DIRECTORY');
	if (! defined $href ) {
		print "Fehler\n";
		Fatal ("Fehler beim Einlesen der Projektinformationen");
	}

	if ( scalar (keys %{$href}) == 0 ) {
		print "OK - keine Projekte vorhanden\n";
		return;
	}

	print "OK\n";
	print "=> Ersetze Runtimelibraries in den vorhandenen Projekten...\n";

	my ($project, $dir);
	while ( ($project, $dir) = each %{$href} ) {
		print "\t$project: ";

		# erst die evtl. noch vorhandene alte Bibliothek
		# löschen
		unlink "$dir/prod/cgi-bin/CIPP_Runtime.pm"
			if -f "$dir/prod/cgi-bin/CIPP_Runtime.pm";
			
		# u.U. noch lib/CIPP Verzeichnis anlegen
		eval {
			mkpath ( [ "$dir/prod/lib/CIPP" ], 0, 0770 );
		};
		if ( $@ ) {
			print "konnte $dir/prod/lib/CIPP nicht erzeugen: $@";
		}

		# CIPP::Runtime ins prod/lib Verzeichnis kopieren
		if ( ! copy ("./lib/CIPP/Runtime.pm",
		      "$dir/prod/lib/CIPP/Runtime.pm") ) {
			print "Fehler beim Kopieren von ./lib/CIPP/Runtime.pm: $!\n";
		}
	}
	print "\n";
}


sub Init_Drivers {
	print "=> Initialisiere Driver-Konfiguration... ";

	unlink <$IDE::Driver_File.*>;
	my $df = new Struct_File ($IDE::Driver_File);

	if ( $Struct_File::init_status != $Struct_File::TRUE ) {
		print "Fehler!\n";
		Fatal ("Driver-Konfigurationsdatei konnte nicht angelegt werden! $IDE::Driver_File $Struct_File::init_status");
	}

	my ($entry);
	foreach $entry (@Cfg::Drivers) {
		$df->Write ( @{$entry} );
	}

	print "Ok\n";

	$df = undef;
}


sub Init_Passwd {
	print "=> Initialisiere Passwort-Datei... ";

	if ( -f "$IDE::Passwd_File.lock" ) {
		print "Warnung!\n\n";
		print <<_EOL;
Die Passwort-Datei existiert bereits! Wenn diese nun initialisiert wird,
werden alle existierenden User geloescht und nur der spirit User neu angelegt.

_EOL
		print "Zum Initialisieren antworten Sie bitte mit 'j' [n]: "; 
		my $answer;
		chomp ($answer = <STDIN>);
		$answer =~ s/\s+$//;

		if ( $answer eq 'j' ) {
			print "\n=> Loesche exisitierende Passwort-Datei... ";
			my $error;
			unlink <$IDE::Passwd_File.*> or ($error=$!);
			if ( $error ne '' ) {
				print "Fehler!\n";
				Fatal ( "Passwort-Datei konnte nicht geloescht ".
					"werden:\n$error");
			}
			print "Ok\n";
			print "=> Initialisiere Passwort-Datei... ";
		} else {
			print "\n=> Ueberspringe Passwort-Datei-Initialisierung... Ok\n";
			return;
		}
	}

	my $pwd = new Passwd ($IDE::Passwd_File);
	my $err;

	if ( ($err = $pwd->Create_User("spirit","spirit","PROJECT,USER","")) != 1 ) {
		print "Fehler!\n";
		Fatal ("Passworddatei konnte nicht angelegt werden! ($err)");
	} else {
		print "Ok\n";
	}
	$pwd = undef;
}

sub Init_Config {
	print "=> Initialisiere Benutzer-Konfigurationsdatei... ";

	if ( -f $IDE::Config_File.".lock" ) {
		print "Warnung!\n\n";
		print <<_EOL;
Die Benutzer-Konfigurations-Datei existiert bereits! Wenn diese nun
initialisiert wird, werden die Einstellungen aller existierenden User
geloescht und nur Grundeinstellungen fuer den spirit-User vorgenommen.

_EOL
		print "Zum Initialisieren antworten Sie bitte mit 'j' [n]: "; 
		my $answer;
		chomp ($answer = <STDIN>);
		$answer =~ s/\s+$//;

		if ( $answer eq 'j' ) {
			print "\n=> Loesche exisitierende Benutzer-Konfigurations-Datei... ";
			my $error;
			unlink <$IDE::Config_Dir/*> or ($error=$!);
			if ( $error ne '' ) {
				print "Fehler!\n";
				Fatal ( "Benutzer-Konfigurationsdatei konnte nicht geloescht ".
					"werden:\n$error");
			}
			print "Ok\n";
			print "=> Initialisiere Benutzer-Konfigurationsdatei... ";
		} else {
			print "\n=> Ueberspringe Benutzer-Konfigurationsdatei-Initialisierung... Ok\n";
			return;
		}
	}

	my $Configure = new Configure ( $IDE::Config_File, "spirit" );

	if ( ! defined $Configure ) {
		print "Fehler\n";
		Fatal  ("Benutzer-Konfigurationsdatei konnte nicht ".
			"initialisiert werden!");
	}

	my ($p, $name, $content);
	foreach $p ( @IDE::Para_Desc ) {
		next if ! defined ($name = $p->[0]);
		eval "\$content = \$IDE:\:$name";
		$Configure->Write('spirit', $name, $content);
	}
	print "Ok\n";
}

sub Print_Success_Message {
	my ($htdocs_url) = @_;

	$htdocs_url = "http://localhost[:port]".$htdocs_url;

	print <<_EOL;

Die Installation wurde erfolgreich abgeschlossen. Wenn Ihr Webserver
entsprechend Ihren Angaben konfiguriert ist, koennen Sie sich unter folgender
URL als Benutzer 'spirit' mit dem Passwort 'spirit' anmelden:

	$htdocs_url

Die Online Dokumentation finden Sie unter

	${htdocs_url}doc/

dimedis wuenscht Ihnen viel Erfolg beim Programmieren mit spirit...

_EOL
}

sub Wait {
	print "Bitte druecken Sie die Enter-Taste! ";
	<STDIN>;
	print "\n";
}

sub Fatal {
	my ($message) = @_;

	print "\nEs ist ein fataler Fehler aufgetreten:\n";
	print $message, "\n";
	print "Die Installation wird abgebrochen.\n\n";
	exit 1;
}

