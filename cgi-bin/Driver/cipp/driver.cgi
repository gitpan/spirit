#!/usr/local/bin/perl

my $DEBUG = 0;

#==============================================================================
#
# PROGRAMM
#	driver.cgi
#
# BESCHREIBUNG
#	spirit Driver-CGI für alle CIPP-Objektypen.
#
#==============================================================================
#
# COPYRIGHT
#	(c) 1997 dimedis GmbH, All Rights Reserved
#
#------------------------------------------------------------------------------
#
# MODIFICATION HISTORY
#	??.??.1997 0.1.0.0 joern
#		Erste Version
#
#	leider über längeren Zeitraum keine History verfügbar :(
#
#	21.01.1998 0.2.0.0 joern@campari
#		+ Anpassungen am DB-Code fuer Sybase und Informix, getrennte
#		  Verwaltung von Datenbanksystem und Datenbankname.
#
#	22.01.1998 0.2.0.1 joern@martini
#		+ neuer Objekttyp: cipp-html
#		  statische HTML-Seite, d.h. wird mit CIPP compiliert, sofort
#		  ausgeführt und die erzeugt HTML-Seite wird ins htdocs
#		  Verzeichnis geschrieben
#		+ Bug: fuer cipp-sql Objekte wird nun beim new_object Event
#		  der Property-Editor aufgerufen, sonst krachts, weil keine
#		  Datenbankzuordnung gemacht wurde
#
#	30.01.1998 0.2.0.2 joern@martini
#		+ zentrale Funktion zum Ermitteln der Produktiv-Datei
#		  zu einem konkreten Objekt
#		  Get_Production_File()
#		+ für folgende Objekttypen wird beim Löschen auch eine
#		  Löschung im Produktivverzeichnis vorgenommen:
#		  cipp, cipp-html, cipp-img, cipp-config, cipp-db
#		+ Image Upload führte zu Laufzeitfehler wegen Verwendung
#		  eines Filhandles via symb. Referenz (nicht erlaubt bei
#		  use strict). Entschärft via "no strict 'refs'".
#
#	11.02.1998 0.2.0.3 joern@martini
#		+ BUGFIX: Beim Loeschen von statischen Seiten wurden die
#		  Dependencies nicht upgedatet!
#
#	27.02.1998 0.2.0.4 joern@martini
#		+ BUGFIX: Beim Speichern eines Bildes, ohne daß bisher ein
#		  Upload stattgefunden hat, gab es einen Laufzeitfehler.
#		  In diesem Fall gibt es nun eine entsprechende Meldung
#		  im Meldungsfenster.
#		+ Bei Ausführung von SQL, Focus auf Ausgabefenster setzen
#		+ Defaultwerte bei Grundeinstellungen (Fehlermeldung) gesetzt
#		+ Bei SQL-Properties wird gesondert angezeigt, wenn keine
#		  Datenbank im System definiert ist. Bei Ausführung eines
#		  solchen Scripts kommt dieselbe Fehlermeldung.
#
#	18.03.1998 0.2.0.5 joern@martini
#		+ Beim Erstellen einer statischen HTML-Datei wird auf
#		  fehlerfreie Ausführung des CIPP Programms geprüft
#
#	19.02.1998 0.2.0.6 joern@martini
#		+ die HTML Laufzeitfehler werden wie CIPP Übersetzungsfehler
#		  formatiert und entsprechend ausgegeben
#		+ Folgende Dependencies werden gepflegt:
#		  CONFIG -> HTML
#		  DB     -> HTML
#
#	05.04.1998 0.2.0.7 joern@home
#		+ Unterstützung von MySQL über DBI
#
#	06.04.1998 0.2.0.8 joern@martini
#		+ Beim CIPP Konstruktor $object_type mitgeben, damit relative
#		  URL's von cipp-html auf cipp-html generiert werden können.
#
#	20.04.1998 0.2.0.9 joern@home
#		+ spirit SQL Datentyp nun auch für MySQL
#
#	06.05.1998 0.2.0.10 joern@martini
#		+ erste Oracle Unterstützung (ohne SQL-Scripts) eingebaut
#
#	13.05.1998 0.3.0.0 joern@martini
#		+ SQL-Script Funktionalität nach SEP Spezifikation B-0.5
#		  eingebaut. D.h. die Ausführung der SQL-Scripts erfolgt
#		  über das externe Programm 'sep.pl'. Dieses kapselt die
#		  Spezialitäten der einzelnen Datenbanksysteme, so daß in
#		  diesem Programm keinerlei datenbankspezifischer Code
#		  mehr enthalten ist.
#		+ als zusätzliches Attribut bei den Datenbankkonfigurationen
#		  wird der Pfad des zu verwendenden SEP's aufgenommen.
#		  Dieses kann auf 'intern' gesetzt werden (dann wird das
#		  spirit-eigene SEP benutzt), oder auf einen beliebigen
#		  Pfad
#
#	14.05.1998 0.4.0.0 joern@martini
#		+ wirkliche generische DBI Unterstützung
#		+ hierzu wird noch das Attribut 'Datasource' bei den
#		  Datenbankkonfigurationen hinzugenommen, welches nur bei
#		  'DBI' als Datenbanksystem zu setzen ist.
#		  Leider werden dadurch einige Parameter bei einigen
#		  Datenbanken doppelt und dreifach gesetzt. (z.B. Informix:
#		  Datasource + Feldangaben + Environment).
#		  Es wäre allerdings eine schlechte Idee, die einzelnen
#		  Informationen aus der Datasource zu extrahieren, weil damit
#		  die Generik für anderen Datenbanksystem weggeworfen wäre.
#		  (z.B. hat Informix diese ätzende databasename@databasesystem
#		  Schreibweise... )
#		  Also lieber die Parameter redundant vorhalten, dafür aber die
#		  Chance auf wirkliche Datenbankunabhängigkeit erhalten.
#		+ Im Ergebnis haben wir nun nur noch zwei 'Datenbanksysteme'
#		  in spirit: DBI und Sybase. Nett.
#
#	15.05.1998 0.4.1.0 joern@martini
#		+ Implementierung von 'make_all', d.h. alle Objekte des
#		  CIPP-Drivers werden neu übersetzt, dabei werden auch
#		  die Dependencies from scratch neu aufgebaut.
#
#	27.05.1998 0.4.2.0 joern@martini
#		+ Anpassungen wegen NT-Portierung
#		  Verwendung von $IDE::OS_temp_dir statt "/tmp" als
#		  Verzeichnus für temporäre Dateien
#
#	25.06.1998 0.4.3.0 joern@martini
#		+ 'use strict' Unterstützung
#		+ zusätzlicher Parameter beim CIPP Konstruktor kommt zunächst
#		  aus der ide.cnf
#
#	01.07.1998 0.4.3.1 joern@martini
#		+ 'persistent' Unterstützung
#		+ zusätzlicher Parameter beim CIPP Konstruktor kommt zunächst
#		  aus der ide.cnf
#
#	20.07.1998 0.4.4.0 joern@martini
#		+ Bug beim Ausführen von SQL-Code bei CIPP_DBI_old Datenbanken
#		  behoben (Datenbanktyp wurde nicht aus Source-String
#		  herausgeholt)
#
#	25.08.1998 0.4.5.0 joern@martini
#		+ <?CONFIG RUNTIME> wird unterstützt.
#		+ <?GETURL RUNTIME> wird unterstützt.
#		+ Beim Driver-Install wird auch ein prod/lib Verzeichnis
#		  angelegt
#
#	27.08.1998 0.4.6.0 joern@martini
#		+ 'use strict' property bei CIPP Objekten eingefügt
#
#	15.09.1998 0.4.7.0 joern
#		- Bugfix: Unter misteriösen Umständen war nach der Bearbeitung
#		  von INCLUDE's (die seltsamerweise ein <?DO> Statement
#		  enthalten mußten), das ursprüngliche Read-Filehandle futsch.
#		  Nach der Analyse des Codes mußte festgestellt werden, daß
#		  dieser Fehler eigentlich IMMER (beim Includen) hätte
#		  auftreten müssen, da als Filehandle ein globales bareword
#		  Filehandle verwendet wurde. Da INCLUDE rekursiv abgearbeitet
#		  werden (durch Kreation einer neuen CIPP Instanz), durfte hier
#		  unter GAR KEINEN UMSTÄNDEN ein globales FileHandle benutzt
#		  werden.
#		  Seit der Verwendung eines objektorientierten FileHandle's
#		  funktioniert es auch in der oben geschilderten Situation
#		  wieder. SEHR SELTSAM!
#		  Dieser Fehler hätte schon viel viel viel früher auftreten
#		  müssen. strange things happens...
#
#	30.09.1998 0.4.8.0 joern
#		- Bugfix: beim Löschen von HTML's wurden die CONFIG-
#		  Abhängigkeiten nicht aktualisiert. Dadurch trat ein Fehler
#		  auf, wenn das entsprechende CONFIG neu übersetzt wurde, weil
#		  die laut Dependency zu übersetzende HTML Seite gar nicht
#		  mehr exisitierte.
#
#	27.10.1998 0.4.8.1 joern
#		- Anpassung an die neue CIPP Version, die auch im Apache
#		  als Modul arbeiten kann. Hier muß im Konstruktor für
#		  den apache_mod Parameter false übergeben werden.
#
#	03.12.1998 0.4.8.2 joern
#		- Anpassung an neue CIPP Version. Das aktuelle Projekt
#		  muß beim Konstruktor mit übergeben werden.
#
#	10.12.1998 0.4.8.3 joern
#		- Neues event 'preprocess' muß verarbeitet werden. Hier
#		  wird das Objekt übersetzt, aber NICHT gespeichert!
#
#	21.12.1998 0.4.8.4 joern
#		- Die Default-Datenbank wird von nun an intern als
#		  PROJEKTNAME.__DEFAULT__ gehandelt, damit die neue
#		  Abhängigkeitsverwaltung, die den Projektanteil im Objekt-
#		  namen ignoriert, damit klar kommt.
#
#	22.12.1998 0.4.8.5 joern
#		- Im Make_All Code werden für jede Abhängigkeitsklasse
#		  die Daten vorm Übersetzen gelöscht.
#
#	18.01.1999 0.5.0.0 joern
#		- CIPP_Runtime.pm -> CIPP::Runtime.pm
#		  Beim Driver-Install wird CIPP::Runtime.pm ins prod/lib
#		  Verzeichnis kopiert
#
#	26.01.1999 0.5.0.1 joern
#		- Wrapping beim Texteditor abgeschaltet
#
#	03.02.1999 0.5.0.2 joern
#		- Bugfix: das Ändern der Default-DB (und ein damit
#		  verbundener Wechsel des Datenbanktreibers) hatte kein
#		  Neuübersetzen zur Folge
#
#------------------------------------------------------------------------------

# Konfigurationsdatei einlesen

BEGIN {
	$0 =~ m!^(.*)[/\\][^/\\]+$!;    # Windows NT Netscape Workaround
	chdir $1;
	require "../../../etc/ide.cnf";
	unshift ( @INC, $IDE::Lib);
#	print STDERR "$0: alive\n";
}

# Diese Subroutine an dieser Stelle, damit ganz sicher keine lex. Variablen
# in den Sichtbereich des eval gelangen!

sub eval_perl_code {
	my ($__PERL_CODE_SREF__) = @_;
#	return "";

	open (PX, "| perl - __no_cgi_input_params_please=1")
		or die "can't fork";
	print PX $$__PERL_CODE_SREF__;
	close PX;

	return "";
	
	no strict;
	eval $$__PERL_CODE_SREF__;
	
	return $@;
}

$main::logger_file = "c:/cipp.log";

# Module einbinden
use strict;	# bin halt Masochist :) (will aber Fehler schneller finden)
use Driver;	# spirit Driver Klasse fuer die ganze laestige Arbeit
use CIPP;	# Der CIPP Praeprozessor
use Param;	# Verwaltung von Parametern in Hashes bzw. Strings
use Cwd;
use IPC::Open2;
use Config;

use File::Path;	# Verzeichnisse anlegen / loeschen und so
use File::Copy;	# zum Kopieren
use FileHandle;

# Zuordnung Objekttypen zu Abhaenigkeitsklassen

my %dep_class = ( 'cipp-inc',	 'include',
		  'cipp-img',	 'image',
		  'cipp-db',	 'db',
		  'cipp-config', 'config' ) ;

my %dep_desc = ( 'cipp-inc',	 'Include-Objekte',
		 'cipp-img',	 'Bilder',
		 'cipp-db',	 'Datenbanken',
		 'cipp-config',	 'Konfigurationen' );

# Driver Objekt holen, gleichzeitig werden die Zugriffsrechte geprueft.
# Bei mangelnden Zugriffsrechten oder fehlenden Aufrufparametern
# wird das Programm an dieser Stelle automatisch beendet und es wird
# eine entsprechende HTML formatierte Fehlermeldung herausgegeben.

my $Driver = new Driver ("cipp", $DEBUG);

if ( 0 and not $DEBUG ) {
	open (DEBUG, "> $IDE::OS_temp_dir/form.txt") or die "can't write $IDE::OS_temp_dir/form.txt";
	$Driver->{query}->save(\*DEBUG);
	close DEBUG;
}

# welcher Objekttyp wird denn nun genau bearbeitet?

my $object_type = $Driver->{object_type};

if ( $object_type eq 'cipp-inc' or $object_type eq 'cipp-config' ) {
	$Driver->{has_depend_object_types} = 1;
}

# Nun holen wir uns das Event ab, um zu wissen, was wir jetzt eigentlich
# genau machen muessen

my $event = $Driver->{event};

# Jetzt kommt der Event-Handler, je nach dem was in $event steht, werden
# die entsprechenden Funktionen aufgerufen. Diese bekommen immer
# eine Referenz auf das Driver-Objekt uebergeben, da in diesem alle
# benoetigten Informationen gespeichert sind und vor allem ueber dieses
# eine ganze Reihe von Standardmethoden aufgerufen werden koennen, die
# die einem ganze Dr*ckarbeit abnehmen.

# print STDERR "event=$event\n";
# print STDERR "source=",$Driver->{query}->param('source'), "\n";

if ( $event eq 'driver_install' ) {		# Driver wird installiert
	Driver_Install ($Driver);
} elsif ( $event eq 'new_object' ) {		# Objekt wurde gerade erzeugt
	New_Object ($Driver);
} elsif ($event eq 'edit' ) {			# Editor-Seite aufbauen
	Editor ($Driver);
} elsif ( $event eq 'save' ) {			# Objekt speichern
	Save ($Driver);
} elsif ( $event eq 'properties' ) {		# Properties editieren
	Property_Editor ($Driver);
} elsif ( $event eq 'versions' ) {		# Versionskontrolle
        Version_Management ($Driver);
} elsif ( $event eq 'show_version' ) {		# Version anzeigen
        Version_Show ($Driver);
} elsif ( $event eq 'ask_for_delete' ) {	# Loesch-Nachfrage
        Ask_For_Delete ($Driver);
} elsif ( $event eq 'delete' ) {		# Objekt loeschen
        Delete ($Driver);
} elsif ( $event eq 'show_image' ) {		# Bild herausgeben
	Image_Show ($Driver);
} elsif ( $event eq 'show_depend' ) {		# Abhaengigkeiten zeigen
	Depend_Show ($Driver);
} elsif ( $event eq 'exec_sql' ) {		# SQL-Code ausfuehren
	SQL_Execute ($Driver);
} elsif ( $event eq 'make_all' ) {		# Alle Objekte neu übersetzen
	Make_All ($Driver);
} elsif ( $event eq 'preprocess' ) {		# Objekt nur übersetzen
	Install ($Driver);
}

# Logger ("beendet!\n");
exit;


# Event-Handler-Subroutinen ===================================================

#------------------------------------------------------------------------------
# Objekttyp-unabhaengige Routinen zum Editieren, Speichern, Installieren
# und Loeschen von Objekten:
#	Driver_Install()
#	New_Object()
#	Editor()
#	Save()
#	Install()
#	Ask_For_Delete()
#	Delete()
#	Print_Messages()
#	Get_Production_File()
#------------------------------------------------------------------------------

sub Driver_Install {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $driver_sys_dir = $Driver->{driver_sys_dir};
	my $project_dir = $Driver->{project_dir};

	eval {
		mkpath(["$project_dir/prod/cgi-bin",
			"$project_dir/prod/config",
			"$project_dir/prod/htdocs",
			"$project_dir/prod/lib",
			"$project_dir/prod/lib/CIPP",
			"$project_dir/prod/logs"], 0, 0770);
	};
	die $@ if $@;

	copy("$driver_sys_dir/CIPP_Runtime.pm",
		"$project_dir/prod/lib/CIPP/Runtime.pm")
		or print STDERR "Fehler Project->Create: CIPP_Runtime.pm";

	Save ($Driver);
}

sub New_Object {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $object_type = $Driver->{object_type};

	if ( $object_type eq 'cipp' or $object_type eq 'cipp-sql' ) {
		Property_Editor ($Driver);
	} else {
		Editor ($Driver);
	}
}

sub Editor {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $object_type = $Driver->{object_type};

	if ( $object_type eq 'cipp' or $object_type eq 'cipp-inc' or
	     $object_type eq 'cipp-config' or $object_type eq 'cipp-html' ) {
		Text_Editor ($Driver);
	} elsif ( $object_type eq 'cipp-img' ) {
		Image_Editor ($Driver);
	} elsif ( $object_type eq 'cipp-db' ) {
		DB_Editor ($Driver);
	} elsif ( $object_type eq 'cipp-sql' ) {
		SQL_Editor ($Driver);
	} elsif ( $object_type eq 'cipp-driver-config' ) {
		Driver_Config_Editor ($Driver);
	}
}


sub Save {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $object_type = $Driver->{object_type};
	my $editor_type = $Driver->{query}->param('editor_type');
	my $content;

	if ( $editor_type eq 'property' ) {
		$content = Property_Save ($Driver);
	} elsif ( $editor_type eq 'version' ) {
		$content = Version_Restore ($Driver);
	} elsif ( $editor_type eq 'content' ) {
		if ( $object_type eq 'cipp' or $object_type eq 'cipp-inc' or
		     $object_type eq 'cipp-config' or 
		     $object_type eq 'cipp-sql' or
		     $object_type eq 'cipp-html' ) {
			$content = Text_Save ($Driver);
		} elsif ( $object_type eq 'cipp-img' ) {
			$content = Image_Save ($Driver);
		} elsif ( $object_type eq 'cipp-db' ) {
			$content = DB_Save ($Driver);
		} elsif ( $object_type eq 'cipp-driver-config' ) {
			$content = Driver_Config_Save ($Driver);
		}
	}
	Install ($Driver, $content);
}

sub Install {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. Referenz auf den Inhalt des Objektes
#
# OUTPUT:	-
#
	my ($Driver, $content) = @_;

	my $object_type = $Driver->{object_type};
    
	my $messages;
	if ( $object_type eq 'cipp' or $object_type eq 'cipp-inc' or
	     $object_type eq 'cipp-html' ) {
		# CIPP_Preprocess ruft dann auch CIPP_Install auf
		$messages = CIPP_Preprocess ($Driver);
		Text_Editor ($Driver, $content, $messages);
	} elsif ( $object_type eq 'cipp-config' ) {
		$messages = Config_Install ($Driver, $content);
		Text_Editor ($Driver, $content, $messages);
	} elsif ( $object_type eq 'cipp-img' ) {
		$messages = Image_Install ($Driver, $content);
		Image_Editor ($Driver, $messages);
	} elsif ( $object_type eq 'cipp-db' ) {
		$messages = DB_Install ($Driver, $content);
		DB_Editor ($Driver, $content, $messages);
	} elsif ( $object_type eq 'cipp-sql' ) {
		my $onload = SQL_Prepare_Execute ($Driver, $content);
		SQL_Editor ($Driver, $content, $onload);
	} elsif ( $object_type eq 'cipp-driver-config' ) {
		$messages = Driver_Config_Install ($Driver, $content);
		Driver_Config_Editor ($Driver, $content, $messages);
	}
}

sub Ask_For_Delete {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $object = $Driver->{object};
	my $object_type = $Driver->{object_type};

	my $dep_type = '';
	my $dep_desc = '';

	($dep_type, $dep_desc) = ('include', 'Include') if $object_type eq 'cipp-inc';
	($dep_type, $dep_desc) = ('image',   'Bild')    if $object_type eq 'cipp-img';
	($dep_type, $dep_desc) = ('db',      'Datenbank-Objekt') if $object_type eq 'cipp-db';
	($dep_type, $dep_desc) = ('config',  'Konfigurations-Objekt') if $object_type eq 'cipp-config';

	if ( $dep_type ne '' ) {
		my $Depend = $Driver->Get_Depend_Object ($dep_type);

		# Abhängige aus allen Projekten holen
		my $junkies = $Depend->Get_Depending_Objects ("$object:$object_type", 1);
		$Depend = undef;

		if ( defined $junkies ) {
			print "<B>Von diesem $dep_desc sind noch Objekte abhängig:</B>\n";
			print "<BLOCKQUOTE>\n";
			print "<TT>\n";
			my $junkie;
			foreach $junkie ( sort keys %{$junkies} ) {
				my $tmp = $junkie;
				$tmp =~ s/:.*//;
				print $tmp, "<BR>\n";
			}
			print "</TT>\n";
			print "</BLOCKQUOTE>\n";
		}
		
	}

	if ( $object_type eq 'cipp-db' ) {
		my $default_db = DB_Get_Default($Driver);
		if ( $default_db eq $object ) {
			print "<P><BLOCKQUOTE>\n";
			print "Achtung! Diese Datenbank ist als Default-Datenbank\n";
			print "konfiguriert. Sie m&uuml;ssen ggf.<BR>eine andere Datenbank\n";
			print "als Default-Datenbank markieren, damit alle CGI-Programme\n";
			print "<BR>korrekt &uuml;bersetzt werde k&ouml;nnen!\n";
			print "</BLOCKQUOTE>\n";
		}
	}
}

sub Delete {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $object = $Driver->{object};
	my $object_type = $Driver->{object_type};

	# Fuer alle Objekte, fuer die Dependencies verwaltet werden, muss
	# der entsprechende Eintrag aus der Dependecy-Datenbank geloescht
	# werden

	my @dep_type;

	push @dep_type, 'include'
			if $object_type eq 'cipp' or 
			   $object_type eq 'cipp-inc' or
			   $object_type eq 'cipp-html';
			   
	push @dep_type, 'config' if $object_type eq 'cipp-html';
	push @dep_type, 'image' if $object_type eq 'image';
	
	my $dep_type;
	foreach $dep_type (@dep_type) {
		my $Depend = $Driver->Get_Depend_Object ($dep_type);
		$Depend->Delete_Object ("$object:$object_type");
		$Depend = undef;	# Dependency explizit freigeben
	}

	# Nun noch evtl. spezielle Dinge erledigen, je nach Objekttyp
	if ( $object_type eq 'cipp-db' ) {
		# Beim Loeschen eines Datenbank-Objektes muss auch der Eintrag
		# aus dem CIPP-Datenbank-Hash geloescht werden
		DB_Delete ($Driver);
	}

	# hier werden nun auch noch die entsprechenden Dateien aus dem
	# prod-Tree geloescht

	if ( index (":cipp:cipp-html:cipp-config:cipp-db:cipp-img:",
		    ":".$object_type.":") != -1 ) {
		Delete_Production_File
			($Driver, $object, $object_type);
	}
}

sub Print_Messages {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. Referenz auf Meldungstext
# OUTPUT:	-
#
	my ($Driver, $messages) = @_;

	$$messages = '' if ! defined $$messages;

	return if $Driver->{object_type} eq 'cipp-img' and $$messages eq '';

	my $font = $Driver->{font};

	print <<__HTML_CODE;
	<P>
	</FORM>
	<FORM NAME=Messages>
	$font<B>Meldungen:</B></FONT><BR>
	<TEXTAREA COLS=$USER::Textarea_Cols ROWS=5>$$messages</TEXTAREA>
__HTML_CODE
}

sub Print_Depend_Button {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	1. HTML-Code fuer Dependency-Button
#
	my ($Driver) = @_;;
	my $object = $Driver->{object};
	my $object_type = $Driver->{object_type};
	my $font = $Driver->{font};

	my $driver_url = $Driver->{url}."?".$Driver->{driver_parameter_url}.
			 "&event=show_depend";
	my $target = "CIPP${object}${object_type}";
	$target =~ tr/.-/_/;
	
	my $js = "dep_window=open('$driver_url','$target',
          'scrollbars=yes,width=400,height=400')";

	print <<__HTML;
	  <P>
	  <FORM>
	  $font
	  <INPUT TYPE=BUTTON VALUE="Abh&auml;ngigkeiten ansehen" onClick="$js">
	  </FONT>
	  </FORM>
__HTML
}

sub Depend_Show {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $object = $Driver->{object};
	my $object_type = $Driver->{object_type};
	my $font = $Driver->{font};

	my $driver_url = $Driver->{url};
	my $target = "CIPP${object}${object_type}";
	$target =~ tr/./_/;
	
	$Driver->Print_HTTP_Header();
	$Driver->Print_HTML_Header
		(undef, "Abhängigkeiten für $object ($object_type)");

	print "<SCRIPT>function Open_Object (URL) ".
		 "{ window.opener.location.href = URL;}</SCRIPT>\n";
	print $font, "\n";
	my $text;

	if ( $object_type eq 'cipp' or $object_type eq 'cipp-html' ) {
		$text = "<B>$object ($object_type)</B> ist von folgenden Objekten ".
		        "abhängig:";
	} else {
		$text = "Folgende Objekte sind von <BR><B>$object ".
                        "($object_type)</B> abhängig:";
	}

	my $dependency_table = "";
	my $exist_dependencies;

	if ( $object_type eq 'cipp' or $object_type eq 'cipp-html' ) {
		my ($dep,$ot);
		foreach $ot ( 'cipp-inc', 'cipp-img', 'cipp-db', 'cipp-config' ) {
			my $Depend = $Driver->Get_Depend_Object
					($dep_class{$ot});
			my $href = $Depend->Get_Depends_On
					("$object:$object_type");
			next if ! scalar (keys %{$href});

			$dependency_table .= "<B>".$dep_desc{$ot}."</B><BLOCKQUOTE>\n";
			my ($k, $v, $js);
			my $q = $Driver->{query};

			foreach $k ( sort keys %{$href} ) {
				$v = $href->{$k};
#			while ( ($k,$v) = each %{$href} ) {
				next if $k eq $Driver->{project}.".__DEFAULT__:cipp-db";
				$k =~ s/:(.*)//;
				$js =	"javascript:Open_Object('".
					"$driver_url"."?".
					"ticket=".$q->param('ticket')."&".
					"project=".$q->param('project')."&".
					"object=$k"."&".
					"object_type=$1"."&".
					"event=edit')";
			        $dependency_table .= "<A HREF=\"$js\">$k</A><BR>\n";
				$exist_dependencies = "TRUE";
			}
			$Depend = undef;

			$dependency_table .= "</BLOCKQUOTE><P>\n";
		}

	} else {
		my $Depend = $Driver->Get_Depend_Object
				($dep_class{$object_type});
		my $href = $Depend->Get_Depending_Objects
				("$object:$object_type");
		my ($k, $v, $js);
		my $q = $Driver->{query};

		my $cipp_table = '';
		my $html_table = '';

		foreach $k ( sort keys %{$href} ) {
			$v = $href->{$k};
#		while ( ($k,$v) = each %{$href} ) {
			$k =~ s/:(.*)//;
			$js =	"javascript:Open_Object('".
				"$driver_url"."?".
				"ticket=".$q->param('ticket')."&".
				"project=".$q->param('project')."&".
				"object=$k"."&".
				"object_type=$1"."&".
				"event=edit')";
			if ( $1 eq 'cipp' ) {
				$cipp_table .= "<A HREF=\"$js\">$k</A><BR>\n";
			} elsif ( $1 eq 'cipp-html' ) {
				$html_table .= "<A HREF=\"$js\">$k</A><BR>\n";
			}
			$exist_dependencies = "TRUE";
		}
		$Depend = undef;
		if ( $cipp_table ne '' ) {
			$dependency_table .= "<B>CIPP-Objekte</B><BLOCKQUOTE>\n".
					     $cipp_table."</BLOCKQUOTE><P>\n";
		} 
		if ( $html_table ne '' ) {
			$dependency_table .= "<B>HTML-Objekte</B><BLOCKQUOTE>\n".
					     $html_table."</BLOCKQUOTE><P>\n";
		} 
	}

	my $driver_param_form = $Driver->{driver_parameter_form}.
			 "<INPUT TYPE=HIDDEN NAME=event VALUE=show_depend>";
	unless ( defined $exist_dependencies) {
	    $dependency_table = "keine Abh&auml;ngigkeiten vorhanden";
	}
	print <<__HTML;
	${font}$text</FONT>
        <P><TABLE WIDTH=100% BORDER=1 CELLPADDING=5>
        <TR><TD VALIGN=TOP>$font
        $dependency_table
	</FONT></TD><TD ALIGN=RIGHT VALIGN=TOP BGCOLOR="$USER::Table_Color">$font
	<FORM NAME=Depend METHOD=POST ACTION="$driver_url">
	$driver_param_form
	<INPUT TYPE=BUTTON VALUE="Anzeige Aktualisieren" 
                           onClick=document.Depend.submit()>
	<BR>
	<INPUT TYPE=BUTTON VALUE="Fenster Schließen" onClick="window.close()">
	</FONT>
	</TD></TR></TABLE>
	</FORM>
__HTML


	$Driver->Print_HTML_Footer();
}

sub Get_Production_File {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. Objekt
#		3. Objekttyp
#
# OUTPUT:	1. Produktionsunterverzeichnis
#		2. zu 1. relativer Dateiname
#	      [ 3. Pfad des .info Files für cipp-img ]
#
# DESCRIPTION:	Gibt den vollständigen Dateinamen des zu dem Objekt
#		gehörenden Produktions-Files zurück
#		Legt u.U. Verzeichnisstruktur im prod Bereich bis zum
#		Objekt an.
#
	my ($Driver, $object, $object_type) = @_;

	my ($project) = split (/\./, $object, 2);

	return undef if ! defined $project;

	if ( $project ne $Driver->{project} ) {
		die "Get_Production_File: Projektübergreifende Installation ".
		    "derzeit nicht möglich: $project != ".$Driver->{project};
	}

	my $prod_dir = $Driver->{project_dir}."/prod";
	my $relpath = $object;
	$relpath =~ tr/\./\//;

#	print STDERR "object=$object project=$project relpath=$relpath path_op=$path_op\n";

	my $dirpath = $relpath;
	$dirpath =~ s!/[^/]+$!!;

#	print STDERR "dirpath=$dirpath\n";

	if ( $object_type eq 'cipp' ) {
		MkPath ("$prod_dir/cgi-bin/$dirpath");
		return ("$prod_dir/cgi-bin", "$relpath.cgi");
	} elsif ( $object_type eq 'cipp-html' ) {
		MkPath ("$prod_dir/htdocs/$dirpath");
		return ("$prod_dir/htdocs", "$relpath.html");
	} elsif ( $object_type eq 'cipp-config' ) {
		my $tmp = $object;
		$tmp =~ s/^[^\.]+\.//;
		return ("$prod_dir/config", "$tmp.config");
	} elsif ( $object_type eq 'cipp-db' ) {
		return ("$prod_dir/config", "$object.db-conf");
	} elsif ( $object_type eq 'cipp-img' ) {
		my $info_file = $Driver->{object_path};
		$info_file =~ s!^(.*)/([^/]*)$!$1/.$2!;
		$info_file .= ".info";

		my $filename = $Driver->{header}->Get_Tag ("IMAGE_FILENAME");
		$filename =~ /\.([^\.]+)$/;
		my $ext = $1;

		MkPath ("$prod_dir/htdocs/$dirpath");

		my $image_file = "$relpath.$ext";

		return ("$prod_dir/htdocs", $image_file, $info_file);
	}

	die "Get_Production_File: Handler für $object_type fehlt";
}

sub Delete_Production_File {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. Objekt
#		3. Objekttyp
#
# OUTPUT:	-
#
	my ($Driver, $object, $object_type) = @_;

	my ($prod_dir, $prod_file, $info_file) = Get_Production_File
		($Driver, $object, $object_type);

#	Logger ("Delete_Production_File");

	my $dir_path = $prod_file;
	$dir_path =~ s!/[^/]+$!!;

	if ( $object_type eq 'cipp' or $object_type eq 'cipp-html' ) {
		unlink "$prod_dir/$prod_file";
		RmPath ("$prod_dir", $dir_path);
	} elsif ( $object_type eq 'cipp-img' ) {
#		Logger ("prod_dir=$prod_dir prod_file=$prod_file");
		unlink "$prod_dir/$prod_file", $info_file;
		RmPath ("$prod_dir", $dir_path);
	} else {
		unlink "$prod_dir/$prod_file";
	}
}

#------------------------------------------------------------------------------
# Objekttyp-unabhaengige Routinen zum Editieren von Properties
#	Property_Editor()
#	Property_Save()
#------------------------------------------------------------------------------

sub Property_Editor {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	# Wenn keine Versionsanzeige, Header ausgeben
	if ( $Driver->{event} ne 'show_version' ) {
		$Driver->Print_HTTP_Header();
		$Driver->Print_HTML_Header();
	}

	# Standard-Properties ausgeben
	$Driver->Print_Property_Header();

	my $object_type = $Driver->{object_type};

	# Je nach Objekttype weitere Properties ausgeben
	if ( $object_type eq 'cipp' ) {
	    my $mime_type = $Driver->{header}->Get_Tag ("MIME_TYPE");
	    CIPP_Properties ($Driver, $mime_type);
	} elsif ( $object_type eq 'cipp-sql' ) {
	    my $database = $Driver->{header}->Get_Tag ("SQL_DB");
	    SQL_Properties ($Driver, $database);
	}

	if ( $object_type eq 'cipp' or
	     $object_type eq 'cipp-inc' or
	     $object_type eq 'cipp-html' ) {
		my $use_strict = $Driver->{header}->Get_Tag ("USE_STRICT");
		CIPP_Property_Use_Strict ($Driver, $use_strict);
	}

	# Wenn keine Versionsanzeige, Footer ausgeben
	if ( $Driver->{event} ne 'show_version' ) {
		Print_Depend_Button ($Driver) 
		    unless $Driver->{object_type} eq 'cipp-driver-config' or
			   $Driver->{object_type} eq 'cipp-sql';
		$Driver->Print_Property_Footer();
		$Driver->Print_HTML_Footer();	
	}
}

sub Property_Save {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	# Driver-Tags komplett holen...
	my $driver_tags = $Driver->Get_Driver_Tags();
	my $object_type = $Driver->{object_type};

	# ... und je nach Objekttyp modifizieren
	if ( $object_type eq 'cipp' ) {
		$driver_tags->{MIME_TYPE} = $Driver->{query}->param('cipp_mime_type');
	} elsif ( $object_type eq 'cipp-sql' ) {
		$driver_tags->{SQL_DB} = $Driver->{query}->param('cipp_sql_db');
	}

	if ( $object_type eq 'cipp' or
	     $object_type eq 'cipp-inc' or
	     $object_type eq 'cipp-html' ) {
		$driver_tags->{USE_STRICT} = $Driver->{query}->param('cipp_use_strict') || 'off';
	}
	
	# Objekt einlesen
	my $object_fh = $Driver->{filehandle};
	my $content = '';

	while (<$object_fh>) {
		$content .= $_;
	}

	# Auf's Speichern vorbereiten
	$Driver->Prepare_Save();

	# Driver-Tags (ggf. modifiziert) wieder zurueckschreiben
	$Driver->Put_Driver_Tags ($driver_tags);

	# Neues File zum Schreiben oeffnen und Header + Inhalt reinschreiben
	my $object_path = $Driver->{object_path};
	open (CIPP_OBJECT_SAVE, "> $object_path") or
		die "SAVE: > $object_path";
	$Driver->{header}->Write_IDE_Header ( *CIPP_OBJECT_SAVE );
	print CIPP_OBJECT_SAVE $content;
	close CIPP_OBJECT_SAVE;

	return \$content;
}

#------------------------------------------------------------------------------
# Objekttyp-unabhaengige Routinen zum Versionsmanagement
#	Version_Management()
#	Version_Show()
#	Version_Restore()
#------------------------------------------------------------------------------

sub Version_Management {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
    my ($Driver) = @_;
    
    $Driver->Version_Management();
}

sub Version_Show {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#

    my ($Driver) = @_;

    $Driver->Open_Old_Version();

    $Driver->Print_HTTP_Header();
    $Driver->Print_HTML_Header();
    $Driver->Print_Editor_Header();
    $Driver->Print_Version_Message();

    Editor ($Driver);
    Property_Editor ($Driver);

    $Driver->Print_Editor_Footer();
    $Driver->Print_HTML_Footer();
}

sub Version_Restore {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $object_type = $Driver->{object_type};

	# Bei 'cipp-img' alten Dateinamen merken, um nacher intelligent die
	# Dependencies loszutreten (naemlich nur beim Formatwechsel)

	if ( $object_type eq 'cipp-img' ) {
		$Driver->{cipp_old_image_name} =
			$Driver->{header}->Get_Tag ("IMAGE_FILENAME");
	}

	# Bei 'cipp-db' alten Typ merken, um nacher intelligent die
	# Dependencies loszutreten (naemlich nur beim Typwechsel)

	if ( $object_type eq 'cipp-db' ) {
		my $fh = $Driver->{filehandle};
		my $content = join ("", <$fh>);
		my $db = Scalar2Hash (\$content);
		$Driver->{cipp_old_db_type} =
			$db->{DB_TYPE};
	}

	my $content = $Driver->Version_Restore ();
	return $content;
}

#------------------------------------------------------------------------------
# Generische Routinen fuer Text-Objekttypen: cipp, cipp-inc, cipp-config
#	Text_Editor()
#	Text_Save()
#------------------------------------------------------------------------------

sub Text_Editor {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#	      [ 2. Referenz auf einzusetzenden Quelltext ]
#	      [ 3. Referenz auf einzusetzenden Meldungstext ]
#
# OUTPUT:	-
#
	my ($Driver, $content, $messages) = @_;

#	Logger ("Start Text_Editor");

	if ( ! defined $content ) {
		my $content_buffer = '';
		my $filehandle = $Driver->{filehandle};
		while (<$filehandle>) {
			$content_buffer .= $_;
		}
		close $filehandle;
		$content = \$content_buffer;
	}

	$Driver->HTML_Text_Escape ($content);

	if ( $Driver->{event} ne 'show_version' ) {
#		Logger ("Headersatz ausgeben");
		$Driver->Print_HTTP_Header();
		$Driver->Print_HTML_Header();
		$Driver->Print_Editor_Header();
	}

	my $font = $Driver->{font};
	my $foo = $USER::Textarea_Cols < $USER::Textarea_Rows;	# sonst Warning

	my $wrapping = ($USER::Textarea_Wrap) ? "WRAP=VIRTUAL" : "";
	
	print <<__HTML_CODE;
	<TEXTAREA $wrapping NAME=source COLS=$USER::Textarea_Cols ROWS=$USER::Textarea_Rows
	 >$$content</TEXTAREA>
	<BR>
__HTML_CODE

	# Meldungen und Footer muessen nur ausgegeben werden, wenn das Header-Flag
	# gesetzt ist.

	if ( $Driver->{event} ne 'show_version' ) {
		Print_Messages($Driver, $messages);
		$Driver->Print_Editor_Footer();
		$Driver->Print_HTML_Footer();
	}

#	Logger ("End Text_Editor");
}

sub Text_Save {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $driver_tags = $Driver->Get_Driver_Tags();
	$Driver->Prepare_Save ();
	$Driver->Put_Driver_Tags ($driver_tags);

	my $object_path = $Driver->{object_path};

	open (CIPP_TEXT_SAVE, "> $object_path") or
		die "SAVE: > $object_path";

	my $error = $Driver->{header}->Write_IDE_Header ( *CIPP_TEXT_SAVE );
	
	my $source = $Driver->{query}->param('source');
	if ( $source !~ /\n$/ ) {
		$source .= "\n";
	}

	# Hier werden Zeilenenden angepaßt, unter NT werden sonst Zeilenenden
	# durch \r\r\n abgebildet, anstatt durch \r\n.

	my $newline = chr(13).chr(10);
	$source =~ s/$newline/chr(10)/eog;

	print CIPP_TEXT_SAVE $source;
	close CIPP_TEXT_SAVE;

	return \$source;
}

#------------------------------------------------------------------------------
# Routinen fuer die Objekttypen: cipp, cipp-inc
#	CIPP_Preprocess()
#	CIPP_Update_Depend()
#	CIPP_Install()
#	CIPP_Depend_Preprocess()
#------------------------------------------------------------------------------

sub CIPP_Properties {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. ausgewaehlter Mime-Type
#		3. use strict ?
#
# OUTPUT:	-
#
    my ($Driver, $mime_type, $use_strict) = @_;
    
    $mime_type ||= "text/html";
    
    my $mime_type_popup = CGI::popup_menu (
	"-name" => 'cipp_mime_type',
	"-values" => [ "text/html", "text/plain", "image/gif",
		     "image/jpeg", "cipp/dynamic" ],
	"-default" => $mime_type );

    my $use_strict_checkbox;
    if ( $use_strict eq 'on' ) {
        $use_strict_checkbox = qq{
	   <INPUT TYPE=CHECKBOX NAME=cipp_use_strict CHECKED>
	}
    } else {
        $use_strict_checkbox = qq{
	   <INPUT TYPE=CHECKBOX NAME=cipp_use_strict>
	}
    }

    my $font = $Driver->{font};
    
    print <<__HTML_CODE;
    <P>
    <TABLE BGCOLOR=$USER::Table_Color BORDER=1>
    <TR><TD VALIGN=TOP>
    <TABLE>
    <TR><TD>
    <FONT FACE=$USER::Font SIZE=$USER::Font_Size>
    MIME-Type:
    </FONT>
    </TD><TD VALIGN=TOP>
    <FONT FACE=$USER::Font SIZE=$USER::Font_Size>
    $mime_type_popup
    </FONT>
    </TD></TR>
    </TABLE>
    </TD></TR>
    </TABLE>
__HTML_CODE
}

sub CIPP_Property_Use_Strict {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. use strict ?
#
# OUTPUT:	-
#
    my ($Driver, $use_strict) = @_;
    
    my $use_strict_checkbox;
    if ( $use_strict ne 'off' ) {
        $use_strict_checkbox = qq{
	   <INPUT TYPE=CHECKBOX NAME=cipp_use_strict CHECKED>
	}
    } else {
        $use_strict_checkbox = qq{
	   <INPUT TYPE=CHECKBOX NAME=cipp_use_strict>
	}
    }

    my $font = $Driver->{font};
    
    print <<__HTML_CODE;
    <P>
    <TABLE BGCOLOR=$USER::Table_Color BORDER=1>
    <TR><TD VALIGN=TOP>
    <TABLE>
    <TR><TD>
    <FONT FACE=$USER::Font SIZE=$USER::Font_Size>
    Zwang zur Variablendeklaration:
    </FONT>
    </TD><TD VALIGN=TOP>
    <FONT FACE=$USER::Font SIZE=$USER::Font_Size>
    $use_strict_checkbox Aktivieren
    </FONT>
    </TD></TR>
    
    </TABLE>
    </TD></TR>
    </TABLE>
__HTML_CODE
}

sub CIPP_Preprocess {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#	      [ 2. Referenz auf eine Liste mit zu uebersetzenden Objekten ]
#
# OUTPUT:	1. Referenz auf Messages
#
	my ($Driver, $object_list) = @_;

	# Erstmal das Hash mit den vorhandenen Datenbanken einlesen

	my $handle = new LkTyH ($Driver->{driver_src_dir}."/db");
	my %database_hash = %{$handle->{LkTyH_hash}};
	$handle = undef;

	# Nun die Default-DB aus CIPP-Default-databases Datei rauspopeln

	my $default_db = DB_Get_Default ($Driver);

	# Wenn wir nicht mit einer Liste von zu uebersetzenden Objekten
	# aufgerufen wurden, wird das aktuelle  Objekt nun in eine
	# Verarbeitunsliste gesteckt, die ggf. im Laufe des Prozesses
	# erweitert wird, falls aufgrund von Abhaengigkeiten weitere
	# Objekte uebersetzt werden muessen.

	if ( ! defined $object_list ) {
		$object_list = [ $Driver->{object}.":".$Driver->{object_type} ];
	}

	my $messages = '';

	my ($i, $object, $object_type);

	while ( $i = pop @{$object_list} ) {
		($object, $object_type) = split (":", $i);
		my $header = $Driver->Get_IDE_Header ($object, $object_type);
		my $object_path = $Driver->Get_Object_Path
					($object, $object_type);

		my $mime_type = $header->{MIME_TYPE} || "text/html";
		my $use_strict = $header->{USE_STRICT};

		$use_strict = 1 if $use_strict ne 'off';
		$use_strict = 0 if $use_strict eq 'off';
		
#		print STDERR "$object: use_strict=$use_strict\n";
		
		$mime_type =~ s/^\s+//;

		# So! jetzt geht's ans Eingemachte! Wollen wir den Kram mal
		# uebersetzen und schauen, ob da watt fanuenftiges rauskommt!

		my $perl_code;		# hier kommt der generierte Perl-Code hinein

		my $cipp_fh = new FileHandle;

		if ( open ($cipp_fh, "< $object_path") ) {

			my $CIPP = new CIPP
				( $cipp_fh, \$perl_code,
				  $Driver->{project_src_hash},
				  \%database_hash, $mime_type, $default_db, $object,
				  "# IDE_HEADER_END\n",
				  1, $object_type,
				  $use_strict, $IDE::Persistent, undef,
				  $Driver->{project}, 1 );

			# Hat das Initialisieren des Praeprozessors geklappt?

			if ( !$CIPP->Get_Init_Status ) {
				$messages = "Konnte CIPP Präprozessor nicht aufrufen!";
				close CIPP_OBJECT_READ;
				return \$messages;
			}

			# Nun Uebersetzen, bei Includes brauchen keine Header generiert zu
			# werden, dabei geht's eh nur um einen Syntax-Check.
			# Bei HTMLs soll kein HTTP Header generiert werden.
	
			if ( $object_type eq 'cipp-html' ) {
				$CIPP->Set_Print_Content_Type (0);
			} elsif ( $object_type eq 'cipp-inc' ) {
				$CIPP->Set_Write_Script_Header(0);
			}
		
			$CIPP->Preprocess();

			close (CIPP_OBJECT_READ);

			# Und? Gab's Fehler? Dann melden und ggf. Liste weiter abarbeiten!

			if ( ! $CIPP->Get_Preprocess_Status ) {
				$messages .= "\nEs sind Übersetzungsfehler aufgetreten: $object\n";
				my $msg_arr = $CIPP->Get_Messages();
				$messages .= join ("\n", @{$msg_arr})."\n";
				if ( $object_type eq 'cipp' or
				     $object_type eq 'cipp-html') {
					CIPP_Update_Depend
						($Driver, $CIPP, $object, $object_type);
				}
			} else {

				# Wenn's geklappt hat und es handelt sich um ein CGI-Script
				# (Objekttyp: cipp), dann installieren wird das Ergebnis und
				# machen ein Update auf die Dependencies!

				my ($success, $message);

				if ( $object_type eq 'cipp' ) {
					($success, $message) = CIPP_Install
						($Driver, $CIPP, $object,
						 'cipp', \$perl_code);
					if ( $success ) {
						$messages .=
							"Das CGI-Programm wurde fehlerfrei ".
							"übersetzt und installiert unter...\n".
							$message;
					} else {
						$messages .=
							"Das übersetzte Perl-Script $object enthält ".
							"Compilerfehler:\n".$message;
					}
	
				CIPP_Update_Depend
						($Driver, $CIPP, $object, "cipp");
	
				} elsif ( $object_type eq 'cipp-html' )  {
					($success, $message) = CIPP_Install
						($Driver, $CIPP, $object,
						 'cipp-html', \$perl_code);
					if ( $success ) {
						$messages .=
							"Die HTML-Seite wurde fehlerfrei ".
							"übersetzt und installiert unter...\n".
							$message;
					} else {
						$messages .=
							"Beim Erstellen der HTML-Seite sind ".
							"folgende Perl Laufzeitfehler aufgetreten:\n".
							$message;
					}

					CIPP_Update_Depend
						($Driver, $CIPP, $object, "cipp-html");
				} else {
					# kann nur noch ein Include sein
	
					$messages = "Die Include-Datei ist fehlerfrei!\n";
	
					# Im Falle eines Include-Objektes muessen wir ggf. davon
					# abhaengige Objekte neu übersetzen, es sei denn,
					# der User will das nicht. Schaun'wer mal...
	
					my $no_depend = $Driver->{query}->param('no_depend');
					if ( not $no_depend ) {

						my $Depend = $Driver->Get_Depend_Object ("include");
						my $junkies = $Depend->Get_Depending_Objects
								("$object:cipp-inc");

						if ( defined $junkies ) {
							# Ok, dann geht's munter weiter. Wir tragen
							# die armen Abhaengigen also in unsere
							# Bearbeitunsliste ein...
							my $foo;
							foreach $foo ( keys %{$junkies} ) {
								push @{$object_list}, $foo;
							}
						}

						$Depend = undef;
					}
				}
			}
			$CIPP = undef;
			$messages .= "\n";
		} else {
			$messages .= "FEHLER: Datei '$object_path' konnte nicht zum Übersetzen geöffnet werden!\n";
		}
	}

#	Logger ("End CIPP_Preprocess");

	return \$messages;
}

sub CIPP_Update_Depend {
#
# INPUT:	1. Driver-Referenz
#		2. CIPP-Referenz
#		3. Name des cipp-Objektes, das abhaengig ist
#		
# OUTPUT:
	my ($Driver, $CIPP, $object, $object_type) = @_;

#	Logger ("Start Update_Depend");

	$object_type = "cipp" if ! defined $object_type;

	my $dep_type;
	my %obj_type = ( 'include', 'cipp-inc',
			 'image',   'cipp-img',
			 'db',      'cipp-db',
			 'config',  'cipp-config' ) ;

	foreach $dep_type ( keys %obj_type ) {
		my %depends_on;
		my $used_objects;
		my $Depend = $Driver->Get_Depend_Object ($dep_type);
		
		if ( $dep_type eq 'include' ) {
			$used_objects = $CIPP->Get_Used_Macros();
		} elsif ( $dep_type eq 'image' ) {
			$used_objects = $CIPP->Get_Used_Images();
		} elsif ( $dep_type eq 'db' ) {
			$used_objects = $CIPP->Get_Used_Databases();
		} elsif ( $dep_type eq 'config' ) {
			$used_objects = $CIPP->Get_Used_Configs();
#			print STDERR "used_objects = $used_objects\n";
		}

		if ( defined $used_objects ) {
			my $object;
			foreach $object ( keys %{$used_objects} ) {
				$depends_on{$object.":".$obj_type{$dep_type}}=1;
			}
		}

		$Depend->Modify_Dependencies
			("$object:$object_type", \%depends_on);

		$Depend = undef;
	}

#	Logger ("End Update_Depend");
}

sub CIPP_Install {
#
# INPUT:	1. Driver-Referenz
#		2. Referenz auf das dazugehoerige CIPP-Objekt
#		3. Name des zu installierenden Objektes
#		4. Referenz auf den zu schreibenden Perl-Code
#
# OUTPUT:	1. boolean, 1=OK, 0=Fehler
#		2. Meldung
#
# DESCRIPTION:	Installiert das übersetzte CIPP Programm (Objekttyp 'cipp')
#		bzw. den generierten HTML Output (Objekttyp 'cipp-html') im
#		prod Zweig des Projektes
#
	my ($Driver, $CIPP, $object, $object_type, $perl_code) = @_;

	my ($success, $messages);
	my ($prod_dir, $cgi_file);

#	Logger ("Start CIPP_Install");

	if ( $object_type eq 'cipp' ) {
		($prod_dir, $cgi_file) = Get_Production_File
			($Driver, $object, 'cipp', 'mk');
		$cgi_file = "$prod_dir/$cgi_file";
	} else {
		# fuer cipp-html und cipp-inc
		# muss ein temp. CGI File erstellt werden
		$cgi_file = $Driver->{project_dir}."/prod/cgi-bin/cipp_cgi$$";
	}

	open (CGI_OUTPUT, "> $cgi_file") or
		return (0, "Konnte $cgi_file nicht anlegen");
	print CGI_OUTPUT $$perl_code;
	close CGI_OUTPUT;
	chmod 0755, $cgi_file;

	if ( $object_type eq 'cipp-html' ) {
		my ($prod_dir, $html_file) = Get_Production_File
			($Driver, $object, 'cipp-html', 'mk');

		$html_file = "$prod_dir/$html_file";

		my $cd = $html_file;
		$cd =~ s!/[^/]+$!!;

		$messages = CIPP_Execute2HTML ($Driver, $cd, $perl_code, $html_file);

		if ( ! defined $messages ) {
			$messages = $html_file;
			$success = 1;
		} else {
			$success = 0;
			$messages = CIPP_Format_Perl_Error
					($Driver, $messages, $object, $cgi_file);
		}

		unlink $cgi_file;
	} else {
		my $cd = $cgi_file;
		$cd =~ s!/[^/]+$!!;

		$$perl_code = "if (0) {\n".$$perl_code."}\n";;

		if ( ! $IDE::OS_has_dup_problem ) {
			$messages = CIPP_Execute2HTML
			($Driver, $cd, $perl_code, $IDE::OS_null_device);
		}

		if ( ! defined $messages ) {
			$messages = $cgi_file;
			$success = 1;
		} else {
			$success = 0;
			$messages = CIPP_Format_Perl_Error
					($Driver, $messages, $object, $cgi_file);
		}
	}

#	Logger ("End CIPP_Install");

	return ($success, $messages);
}


sub CIPP_Execute2HTML {
#
# INPUT:	1. Driver-Referenz
#		2. Directory
#		3. Referenz auf Perl-Code
#		4. HTML-Dateiname
#
# OUTPUT:	1. Fehlermeldung oder undef im Erfolgsfall
#
# DESCRIPTION:	Führt das angegebene CGI Script im übergebenen Verzeichnis
#		aus und schreib dessen Ausgabe in die HTML Datei.
#		Evtl. auftretende Fehler werden zurückgegeben.
#
	my ($Driver, $dir, $perl_code, $catch_file) = @_;

	open (DBG, "> $IDE::OS_temp_dir/cipp");
	print DBG $$perl_code;
	close DBG;

#	return "Testfehler";

#	Logger ("Start CIPP_Execute2HTML");

	no strict 'refs';

	# In das CGI Verzeichnis wechseln

	my $cwd_dir = cwd();
	chdir $dir
		or return "Konnte nicht nach Verzeichnis '$dir' wechseln";

	# STDOUT auf die Datei umleiten

#	print STDERR "hiho\n";

	my $save_stdout = "save_stdout".(++$main::cipp_save_stdout);
	if ( ! open ($save_stdout, ">&STDOUT") ) {
		chdir $cwd_dir;
		return "Konnte STDOUT nicht duplizieren";
	}

	close STDOUT;
	if ( ! open (STDOUT, "> $catch_file") ) {
		open (STDOUT, ">&$save_stdout")
			or die "Konnte STDOUT nicht restaurieren";
		close $save_stdout;
		chdir $cwd_dir;
		return "Konnte '$catch_file' nicht zum Schreiben öffnen";
	}

	# STDERR umleiten

	my $save_stderr = "save_stderr".($main::cipp_save_stdout);
	if ( ! open ($save_stderr, ">&STDERR") ) {
		chdir $cwd_dir;
		open (STDOUT, ">&$save_stdout")
			or die "Konnte STDOUT nicht restaurieren";
		close $save_stdout;
		return "Konnte STDERR nicht duplizieren";
	}

	my $catch_stderr = "$IDE::OS_temp_dir/cipp_stderr$$";

	close STDERR;
	if ( ! open (STDERR, "> $catch_stderr") ) {
		open (STDOUT, ">&$save_stdout")
			or die "Konnte STDOUT nicht restaurieren";
		open (STDERR, ">&$save_stderr")
			or die "Konnte STDERR nicht restaurieren";
		close $save_stdout;
		close $save_stderr;
		chdir $cwd_dir;
		return "Konnte '$catch_stderr' nicht zum Schreiben öffnen";
	}

#	print STDERR "fugging fehla\n";

	# Löschen des Error-Handlers und Setzen der Variablen
	# $_cipp_no_error_handler. Das verhindert bei dem eval des Scripts das
	# erneute Setzen des Error-Handlers

	$CIPP_Exec::_cipp_in_execute = 1;
	$CIPP_Exec::_cipp_no_http = 1;
	my $old_cipp_error_handler = $main::SIG{__DIE__};
	$main::SIG{__DIE__} = undef;

	# CGI-Script ausführen, Error-Code merken, Error-Handler zurücksetzen
#	{
#		no strict;
#		eval $$perl_code;
#	}

	my $error = eval_perl_code ($perl_code);
	$main::SIG{__DIE__} = $old_cipp_error_handler;

	# wieder ins aktuelle Verzeichnis zurückwechseln

	chdir $cwd_dir;

	# Umleitungsdatei wieder schließen und STDOUT restaurieren

	close STDOUT;
	open (STDOUT, ">&$save_stdout")
		or return "Konnte STDOUT nicht restaurieren";
	close $save_stdout;

	# STDERR Umleitung wieder schließen und STDERR restaurieren

	close STDERR;
	open (STDERR, ">&$save_stderr")
		or return "Konnte STDERR nicht restaurieren!";
	close $save_stderr;

	# Und? Hat das geklappt, oder müssen wir eine Fehlermeldung
	# zusammenbauen?

	open ($save_stderr, $catch_stderr)
		or die "Konnte $catch_stderr nicht öffnen";
	$error .= join ("", <$save_stderr>);
	close $save_stderr;
	unlink $catch_stderr;

	$error =~ s/^.*?syntax ok.*?\n//i;

	if ( $error ne '' ) {
		unlink $catch_file;
	}

#	Logger ("End CIPP_Execute2HTML");

	return $error if $error ne '';
	return undef;
}



sub CIPP_Format_Perl_Error {
#
# INPUT:	1. Driver-Referenz
#		2. Perl Fehlermeldung
#		3. Objektname
#		4. dazugehörige CGI-Datei, die den Fehler verursacht hat
#
# OUTPUT:	1. Fehlermeldung im CIPP-Format:
#		"object\tline\t<?CIPP-Tag>: Message"
#
	my ($Driver, $message, $object, $cgi_file) = @_;

	return "\n$message";
	
	# Die folgende Routine ist im Moment Scheiße. Sie arbeitet nur
	# sinnvoll, wenn maximal EIN Fehler aufgetreten ist...
	

#	print STDERR "message: $message\n";

	$message =~ s/\s+at\s+\(eval\s+\d+\)\s+line\s+(\d+)//m;
	my $perl_line = $1;
#	print STDERR "perl_line=$perl_line\n\n";

	my ($cipp_line, $cipp_tag, $cipp_tag_line);

	my $fh = new FileHandle;
	open ($fh, $cgi_file) or die "Konnte $cgi_file nicht öffnen";

	my $line = 0;
	while (<$fh>) {
		++$line;
		if ( /^#\s+cippline\s+(\d+)\s+\"([^\"]+)/ ) {
#			print STDERR "found: $line $_";
			$cipp_line = $1;
			$cipp_tag = $2;
			$cipp_tag_line = $line;
		}
		last if $line == $perl_line;
	}
	close $fh;

	if ( ! defined $cipp_line ) {
		return "$object\t??\t<??>: $message";
	}

	if ( $line > $cipp_tag_line + 1 ) {
		$cipp_line = $cipp_line."(+".($line - $cipp_tag_line - 1).")";
	}

	$cipp_tag =~ s/$object:?&lt;/</;

	return "$object\t$cipp_line\t$message" if $cipp_tag eq $object;
	return "$object\t$cipp_line\t$cipp_tag: $message";
}

sub CIPP_Depend_Preprocess {
#
# INPUT:	1. Driver-Referenz
#		2. Objekt, das sich geaendert hat
#		3. dessen Objekttyp
#		4. Abhaengigkeitsklasse
#
# OUTPUT:	1. Referenz auf Messages
#
	my ($Driver, $object, $object_type, $dep_class) = @_;

	$object ||= '';

	my $messages = '';
	my $junkies;

	my $Depend = $Driver->Get_Depend_Object ($dep_class);
	$junkies = $Depend->Get_Depending_Objects ("$object:$object_type");

#	print STDERR "DEPEND: object=$object, junkies=$junkies\n";

	my @object_list;

	if ( defined $junkies ) {
		# Wir tragen die armen Abhaengigen also in unsere
		# Bearbeitunsliste ein...
		my $foo;
		foreach $foo ( keys %{$junkies} ) {
			next if $object_type eq 'cipp-config' and
				$foo =~ /:cipp$/;
			push @object_list, $foo;
		}
		$messages .= ${ CIPP_Preprocess ($Driver, \@object_list) };
	}

	$Depend = undef;

	return \$messages;
}


#------------------------------------------------------------------------------
# Routinen fuer Config-Objekttyp: cipp-config
#	Config_Install()
#------------------------------------------------------------------------------

sub Config_Install {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
# BEMERKUNG:	Das Driver-Objekt muss sich im Prepare_Save() Zustand befinden
#
	my ($Driver) = @_;

	my $object_path = $Driver->{object_path};

	open (CIPP_CONFIG, "< $object_path") or
		die "CIPP_CONFIG: < $object_path";
	while (<CIPP_CONFIG>) {
		last if $_ eq "# IDE_HEADER_END\n";
	}

	my $object = $Driver->{object};
	my ($prod_dir, $config_file) = Get_Production_File
			($Driver, $object, 'cipp-config','mk');
	$config_file = "$prod_dir/$config_file";

	open (CONFIG_OUTPUT, "> $config_file") or
		die "CONFIG_OUTPUT: > $config_file";

	while (<CIPP_CONFIG>) {
		next if /^\s*#/;
		s/\r//;
		next if /^[\s]*$/;
		print CONFIG_OUTPUT;
	}
	print CONFIG_OUTPUT "\n1;\n";
	close CONFIG_OUTPUT;
	close CIPP_CONFIG;

	my $message = "Konfigurationsdatei gespeichert unter...\n".$config_file."\n\n";

	if ( not $Driver->{query}->param('no_depend') ) {
		$message .= ${CIPP_Depend_Preprocess
		       ($Driver, $object, "cipp-config", "config")};
	}
	
	return \$message;
}

#------------------------------------------------------------------------------
# Routinen fuer Bild-Objekttyp: cipp-img
#	Image_Editor()
#	Image_Show()
#	Image_Save()
#	Image_Install()
#------------------------------------------------------------------------------

sub Image_Editor {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#	      [ 2. Referenz auf Messages ]
#
# OUTPUT:	-
#
	my ($Driver, $messages) = @_;
	my $version = '';

	if ( $Driver->{event} ne 'show_version' ) {
		$Driver->Print_HTTP_Header();
		$Driver->Print_HTML_Header();
		$Driver->Print_Editor_Header(undef, "multipart/form-data");
	} else {
		$version = "&version=".$Driver->{query}->param('version');
	}


	my $img_src = '<IMG SRC="'.$Driver->{url}.'?'.$Driver->{driver_parameter_url}.
		      '&event=show_image'.$version.'">';

	my $font = $Driver->{font};
	my $filename = $Driver->{header}->Get_Tag("IMAGE_FILENAME");

	print <<__HTML_CODE;
	<P>
	<TABLE BGCOLOR="$USER::Table_Color" BORDER=1 CELLPADDING=5>
	<TR><TD>
	  $img_src<BR>
        </TD></TR>
	<TR><TD>
	  ${font}Original Dateiname: <B>$filename</B></FONT>
        </TD></TR>
	<TR><TD>
	  ${font}Neues Bild:<BR>
	  <INPUT TYPE=FILE NAME=filename SIZE=60>
	  </FONT>
	</TR></TD>
	</TABLE>
__HTML_CODE

	if ( $Driver->{event} ne 'show_version' ) {
		Print_Messages($Driver, $messages);
		$Driver->Print_Editor_Footer();
		$Driver->Print_HTML_Footer();
	}
}

sub Image_Show {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;
	my $version;

	if ( $version = $Driver->{query}->param('version') ) {
		$Driver->Open_Old_Version ($version);
	}

	my $mime_type = $Driver->{header}->Get_Tag ("MIME_TYPE");
	my $filehandle = $Driver->{filehandle};

	if ( eof ($filehandle) ) {
		close $filehandle;
		my $no_image_file = $Driver->{driver_sys_dir}."/no_image.gif";
		open ($filehandle, $no_image_file)
			or die "Konnte $no_image_file nicht oeffnen";
		$mime_type = "image/gif";
	} else {
		# NT Workaround: ich HASSE sie...
		close $filehandle;
		open $filehandle, $Driver->{object_path};
		binmode $filehandle;
		while (<$filehandle>) {
			last if /# IDE_HEADER_END/;
		}
	}

	$| = 1;
	binmode STDOUT;

	print "Content-type: $mime_type\n";
	print "Pragma: no-cache\n";
	print "Expires: now\n\n";

	binmode $filehandle;

	my $read_result;
	my $buffer;
	my $len = 0;
	while ( $read_result = read $filehandle, $buffer, 1024 ) {
		print $buffer;
		$len += length($buffer);
	}
#	print STDERR "show_len: $len\r\n";

	close $filehandle;
}

sub Image_Save {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	# Alle Driver-Tags holen
	my $driver_tags = $Driver->Get_Driver_Tags();

	# Alten Dateinamen merken, um nacher intelligent die Dependencies
	# loszutreten
	$Driver->{cipp_old_image_name} = $driver_tags->{IMAGE_FILENAME};

	# Filehandle fuer File-Upload holen, wenn nichts angegeben, auf das
	# aktuelle Objekt setzen, so dass dieses wieder gespeichert wird.

	my $filename;
	my $upload_fh = $Driver->{query}->param('filename');

	if ( $upload_fh eq '' ) {
		$filename = $driver_tags->{IMAGE_FILENAME};
		$upload_fh = $Driver->{filehandle};
		# NT Workaround: ich HASSE sie...
		close $upload_fh;
		open $upload_fh, $Driver->{object_path};
		binmode $upload_fh;
		while (<$upload_fh>) {
			last if /# IDE_HEADER_END/;
		}
	} else {
		$filename = $upload_fh;
	}

	my $image= '';
	{
		# Image einlesen
		no strict qw(refs var);
		package Driver;
		binmode $upload_fh;

		my ($read_result, $buffer);
		
		while ( $read_result = read $upload_fh, $buffer, 1024 ) {
			$image .= $buffer;
		}
		close ($upload_fh);
		
		die "Fehler beim Lesen" if ! defined $read_result;
	}

#	print STDERR "image len=", length($image), "\n";

	# auf's Speichern vorbereiten
	$Driver->Prepare_Save ();

	# IMAGE_FILENAME setzen und Driver-Tags zurueckschreiben
	$driver_tags->{IMAGE_FILENAME} = $filename;
	$Driver->Put_Driver_Tags ($driver_tags);

	# Zieldatei oeffnen, Header und Bild reinschreiben
	my $object_path = $Driver->{object_path};

	open (CIPP_OBJECT_SAVE, "> $object_path") or
		die "SAVE: > $object_path";
	$Driver->{header}->Write_IDE_Header ( *CIPP_OBJECT_SAVE );
	close CIPP_OBJECT_SAVE;

	# nun im Append Modus nochmal öffnen, und dann mit binmode
	# schreiben
	open (CIPP_OBJECT_SAVE, ">> $object_path") or
		die "SAVE: >> $object_path";
	binmode CIPP_OBJECT_SAVE;
	print CIPP_OBJECT_SAVE $image;
	close CIPP_OBJECT_SAVE;

	return \$image;
}

sub Image_Install {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. Referenz auf den Inhalt
#
# OUTPUT:	-
#
	my ($Driver, $content) = @_;

#	print STDERR "content len=", length($$content), "\n";

	my $object = $Driver->{object};
	my $filename = $Driver->{header}->Get_Tag ("IMAGE_FILENAME");

	if ( $filename eq '' ) {
		my $message = "Bild wurde NICHT installiert, es fand noch ".
			      "kein Upload statt!";
		return \$message;
	}

	$filename =~ /\.([^\.]+)$/;
	my $ext = $1;

	my ($prod_dir, $image_file, $info_file) =
		Get_Production_File ($Driver, $object, 'cipp-img','mk');

	$image_file = "$prod_dir/$image_file";

	# nun legen wir fuer CIPP noch eine Datei an, in der der Dateiname
	# steht, unter dem das Bild im htdocs-Bild-Verzeichnis zu finden ist
	# (insbesondere mit der Dateiendung, die das Original-Upload Bild hatte)

	open (IMAGE_INFO, "> $info_file") or
		die "SAVE: > $info_file";
	print IMAGE_INFO "$object.$ext";
	close IMAGE_INFO;

	# Jetzt wird das Bild selber im images Subdirectory installiert

	open (IMG_OUTPUT, "> $image_file") or
		die "IMG_OUTPUT: > $image_file";
	binmode IMG_OUTPUT;
	print IMG_OUTPUT $$content;
	close IMG_OUTPUT;

	my $messages = 	"Das Bild wurde installiert unter...\n".
			"$image_file\n";
	
	# Wenn sich die Dateiendung geaendert hat, muessen nun evtl. noch
	# einige Seiten neu uebersetzt werden
	# Hierzu ziehen wir den alten Dateinamen heran, der in Image_Save() bzw.
	# Version_Restore() gerettet wurde

	my $old_ext = $Driver->{cipp_old_image_name};
	$old_ext =~ /\.([^\.]+)$/;
	$old_ext = $1;

	if ( $ext ne $old_ext ) {
		# Bild mit alter Endung aus prod Tree loeschen
		$image_file =~ s/$ext$/$old_ext/;
		unlink $image_file;
		# Dependencies lostreten
		$messages .= ${CIPP_Depend_Preprocess
			       ($Driver, $object, "cipp-img", "image")};
	}

	return \$messages;
}

#------------------------------------------------------------------------------
# Routinen fuer Datenbank-Objekttyp: cipp-db
#	DB_Editor()
#	DB_Parse_ENV()
#	DB_Save()
#	DB_Install()
#------------------------------------------------------------------------------

sub DB_Editor {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#	      [ 2. Referenz auf Inhalt ]
#	      [ 3. Referenz auf Messages ]
#
# OUTPUT:	-
#
	my ($Driver, $content, $messages) = @_;

	my $object = $Driver->{object};
	my $driver_tags = $Driver->Get_Driver_Tags();

	if ( $Driver->{event} ne 'show_version' ) {
		$Driver->Print_HTTP_Header();
		$Driver->Print_HTML_Header();
		$Driver->Print_Editor_Header();
	}

	# Wenn Inhalt nicht uebergeben, aus Objektdatei lesen

	if ( ! defined $content ) {
		my $content_buffer = '';
		my $filehandle = $Driver->{filehandle};
		while (<$filehandle>) {
			s/\r//;
			$content_buffer .= $_;
		}
		close ($filehandle);
		$content = \$content_buffer;
	}

	# Dann ueberfuehren wir den Inhalt mal in eine schoene
	# Hash-Struktur

	my $db = Scalar2Hash ($content);

	my $db_type = $db->{DB_TYPE};
	my $db_name = $db->{DB_NAME} || "";
	my $db_user = $db->{DB_USER} || "";
	my $db_env  = $db->{DB_ENV} || "";
	my $db_system = $db->{DB_SYSTEM} || "";
	my $db_cmd = $db->{DB_CMD} || "";
	my $db_sep = $db->{DB_SEP} || "";
	my $db_source = $db->{DB_SOURCE} || "";

	my $db_autocommit = $db->{DB_AUTOCOMMIT} || " An";

	$$messages .= DB_Parse_ENV($db);

	my $db_pass = "";

	my $db_type_popup = CGI::popup_menu (
	"-name" => 'db_type',
	"-values" => [ "CIPP_DB_DBI",
		       "CIPP_DB_DBI_old" ],
#		       "CIPP_DB_Sybase" ],
	"-labels" =>  { "CIPP_DB_DBI" => "DBI",
			"CIPP_DB_DBI_old" => "DBI 0.73 (OAS)" },
#		       "CIPP_DB_Sybase" => "Sybase" },
	"-default" => $db_type,
	"-onChange" =>
	q{
		if ( document.IDE_Functions.db_type.options
		     [document.IDE_Functions.db_type.selectedIndex].value == 'CIPP_DB_DBI' ) {
			document.IDE_Functions.db_source.value = old_db_source;
		} else {
			old_db_source = document.IDE_Functions.db_source.value;
			document.IDE_Functions.db_source.value = '';
		}
	}
	);

	# Default Datenbank?
	my $default_db = DB_Get_Default($Driver);
	my $db_default_switch = $default_db eq $object ? " Ja" : " Nein";

	my $default_radio = CGI::radio_group (
	"-name" => 'db_default',
	"-values" => [ " Ja", " Nein" ],
	"-default" => $db_default_switch,
	"-linebreak" => 0 );

	my $autocommit_radio = CGI::radio_group (
	"-name" => 'db_autocommit',
	"-values" => [ " An", " Aus" ],
	"-default" => $db_autocommit,
	"-linebreak" => 0 );

	my $font = $Driver->{font};

	print <<__HTML_CODE;
	<SCRIPT LANGUAGE="Javascript">
	var old_db_source = '$db_source';
	</SCRIPT>
	<P>
	<TABLE BGCOLOR="$USER::Table_Color" BORDER=1 CELLPADDING=2>
	<TR><TD>
	  ${font}Datenbanktyp:
	  </FONT>
	</TD><TD>
	  ${font}
	  $db_type_popup
	</TD></TR>
	<TR><TD>
	  ${font}Datenquelle (nur bei DBI):
	  </FONT>
	</TD><TD>
	  ${font}
	  <INPUT TYPE=TEXT NAME=db_source SIZE=40 VALUE="$db_source"
                 onFocus="if ( document.IDE_Functions.db_type.options
		     [document.IDE_Functions.db_type.selectedIndex].value
		     == 'CIPP_DB_Sybase' ) {
			alert ('Eine Datenquelle muß nur bei der Verwendung von DBI angegeben werden');
			document.IDE_Functions.db_system.focus();
		}">
	</TD></TR>
	<TR><TD>
	  ${font}
	  Name des Datenbanksystems:
	  </FONT>
	</TD><TD>
	  ${font}
	  <INPUT TYPE=TEXT NAME=db_system SIZE=40 VALUE="$db_system">
	  </FONT>
	</TD></TR>
	<TR><TD>
	  ${font}
	  Name der Datenbank:
	  </FONT>
	</TD><TD>
	  ${font}
	  <INPUT TYPE=TEXT NAME=db_name SIZE=40 VALUE="$db_name">
	  </FONT>
	</TD></TR>
	<TR><TD>
	  ${font}
	  Benutzername:
	  </FONT>
	</TD><TD>
	  ${font}
	  <INPUT TYPE=TEXT NAME=db_user SIZE=40 VALUE="$db_user">
	  </FONT>
	</TD></TR>
	<TR><TD>
	  ${font}
	  Password:<BR>
	  </FONT>
	</TD><TD>
	  ${font}
	  <INPUT TYPE=PASSWORD NAME=db_pass SIZE=40 VALUE="$db_pass">
	  </FONT>
        </TD></TR>
	<TR><TD>
	  ${font}Autocommit per Default... 
	  </FONT>
	</TD><TD>
	  ${font}$autocommit_radio</FONT>
	</TD></TR>
	<TR><TD>
	  ${font}Default-Datenbank? 
	  </FONT>
	</TD><TD>
	  ${font}$default_radio</FONT>
	</TD></TR>
	<TR><TD>
	  ${font}
	  Kommando für interaktives SQL:
	  </FONT>
	</TD><TD>
	  ${font}
	  <INPUT TYPE=TEXT NAME=db_cmd SIZE=40 VALUE="$db_cmd">
	  </FONT>
	</TD></TR>
	<TR><TD>
	  ${font}
	  Pfad des zu verwendenden SEP:
	  </FONT>
	</TD><TD>
	  ${font}
	  <INPUT TYPE=TEXT NAME=db_sep SIZE=40 VALUE="$db_sep">
	  </FONT>
	</TD></TR>
	<TR><TD COLSPAN=2>
	  ${font}Umgebungsvariablen:</FONT><BR>
	  <TEXTAREA NAME=db_env ROWS=4 COLS=60>$db_env</TEXTAREA>
	</TR></TD>
	</TABLE>
__HTML_CODE

	if ( $Driver->{event} ne 'show_version' ) {
		Print_Messages($Driver, $messages);
		$Driver->Print_Editor_Footer();
		$Driver->Print_HTML_Footer();
	}
}

sub DB_Parse_ENV {
#
# INPUT:	1. Hashreferenz auf Datenbank-Parameter
#		   (insbesondere ->{DB_ENV})
#
# OUTPUT:	1. Fehlermeldung
#
# DESCRIPTION:	Parsed $1->{DB_ENV} und schreibt das Ergebnis in
#		$1->{DB_ENV_HASH}->{PAR} = Value.
#
	my ($db) = @_;

	my $db_env = $db->{DB_ENV};
	my $message = '';

	$db_env =~ s/\r//g;
	my @e = split ("\n", $db_env);
	my $e;

	while ( $e = shift @e and ! $message ) {
		$e =~ s/^\s+//;
		$e =~ s/\s+$//;
		$e =~ /^([^\s]+)\s+(.+)$/;
		my ($n, $v) = ($1, $2);
		if ( !defined $n or !defined $v ) {
			$message = "Syntaxfehler bei Environmentvariablen\n";
		} else {
			$db->{DB_ENV_HASH}->{$n} = $v;
		}
	}

	return $message;
}


sub DB_Save {
#
# INPUT:	1. Referenz auf das Driver-Objekt
# 
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $object = $Driver->{object};

	my $driver_tags = $Driver->Get_Driver_Tags();
	my $q = $Driver->{query};

	my %db;

	# die Formularvariablen in ein Hash schreiben

	$db{DB_NAME} = $q->param('db_name');
	$db{DB_USER} = $q->param('db_user');
	$db{DB_PASS} = $q->param('db_pass');
	$db{DB_TYPE} = $q->param('db_type');
	$db{DB_SYSTEM} = $q->param('db_system');
	$db{DB_CMD}  = $q->param('db_cmd');
	$db{DB_SEP}  = $q->param('db_sep');
	$db{DB_SOURCE} = $q->param('db_source');
	$db{DB_ENV}  = $q->param('db_env');
	$db{DB_AUTOCOMMIT} = $q->param('db_autocommit');

	$db{DB_ENV}  =~ s/\r//g;

	# altes Objekt einlesen, um -> evtl. altes Password zu uebernehmen,
	#			    -> Datenbanktypaenderung zu bemerken

	my ($old_content, $old_fh);
	$old_fh = $Driver->{filehandle};
	$old_content = join ("", <$old_fh>);
	my $old_db = Scalar2Hash (\$old_content);

	# Wenn kein neues Password eingegeben, nehmen wir das alte

	if ( $db{DB_PASS} ne '' ) {
                my $x;
		$db{DB_PASS} =~ s/(.)/($x=chr(ord($1)^85),ord($x)>15)?(sprintf("%%%x",ord($x))):("%0".sprintf("%lx",ord($x)))/eg;
	} else {
		$db{DB_PASS} = $old_db->{DB_PASS};
	}

	# Datenbanktyp merken, um spaeter Dependencies nur wirken zu lassen,
	# wenn sich der Typ geaendert hat

	$Driver->{cipp_old_db_type} = $old_db->{DB_TYPE};

	my $default_db = DB_Get_Default($Driver);
	$default_db ||= '';

	# Ist diese Datenbank jetzt Default-Datenbank und war es vorher nicht?

	if ( $q->param('db_default') eq ' Ja' and $default_db ne $object ) {
		# Dann speichern!
		DB_Set_Default ($Driver, $object);
		# Und merken uns, dass sich an der Default-DB Einstellung was
		# geaendert hat, denn da greifen nachher die Dependencies
		$Driver->{cipp_process_default_db_scripts} = 1;
	}

	# War diese Datenbank bisher Default-DB und ist es jetzt nicht mehr?

	if ( $q->param('db_default') eq ' Nein' and $default_db eq $object ) {
		# Dann speichern wir das
		DB_Set_Default ($Driver, '');
		# Und merken uns, dass sich an der Default-DB Einstellung was
		# geaendert hat, denn da greifen nachher die Dependencies
		$Driver->{cipp_process_default_db_scripts} = 1;
	}

	my $source = Hash2Scalar (\%db);

	$Driver->Prepare_Save ();
	$Driver->Put_Driver_Tags ($driver_tags);

	my $object_path = $Driver->{object_path};
	open (DB_SAVE, "> $object_path") or
		die "SAVE: > $object_path";
	$Driver->{header}->Write_IDE_Header ( *DB_SAVE );
	print DB_SAVE $$source, "\n";
	close DB_SAVE;

	return $source;
}

sub DB_Install {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. Rerefenz auf den Inhalt
#
# OUTPUT:	1. Messages
#
	my ($Driver, $content) = @_;

	my $db = Scalar2Hash($content);

	my $parse_messages = DB_Parse_ENV ($db);
	my $messages = '';

	if ( $parse_messages eq '' ) {
		# Dann wollen wir mal ein schoenes Konfigurationsfile fuer diese
		# Datenbank wegschreiben

		my $object = $Driver->{object};
		my ($prod_dir, $filename) = Get_Production_File
					($Driver, $object, 'cipp-db','mk');
		$filename = "$prod_dir/$filename";

		my $tmp = $object;
		$tmp =~ s/^[^\.]+\.//;
		my $package = "\$cipp_db_$tmp";
		$package =~ s/\./_/g;

		my $autocommit = ($db->{DB_AUTOCOMMIT} eq ' An') ? 1 : 0;
		
		my $pass = $db->{DB_PASS};

		open (DB_CONF, "> $filename") or die "SAVE: $filename\n";
		print DB_CONF "$package:\:data_source = '",
			      $db->{DB_SOURCE}, "';\n";
		print DB_CONF "$package:\:system = '", $db->{DB_SYSTEM},"';\n";
		print DB_CONF "$package:\:name = '", $db->{DB_NAME},"';\n";
		print DB_CONF "$package:\:user = '", $db->{DB_USER},"';\n";
		print DB_CONF "($package:\:password = q{", $pass,"}) ",
			      "=~ s/%(..)/chr(ord(pack('C', hex(\$1)))^85)/eg;\n";
		print DB_CONF "$package:\:Auto_Commit = $autocommit;\n";

		my ($key, $val);
		while ( ($key,$val) = each (%{$db->{DB_ENV_HASH}}) ) {
			print DB_CONF "\$main::ENV{$key} = '$val';\n";
		}

		print DB_CONF "1;\n";
		close DB_CONF;

		chmod 0660, $filename;

		$messages = "Datenbankkonfiguration wurde installiert unter...\n".
			    "$filename\n\n";

		# Wir machen nun sicherheitshalber noch ein Update auf das
		# Datenbankhash, obwohl dies eigentlich nur notwendig ist,
		# wenn sich der Datenbanktyp auch geändert hat.

		my $db_file = $Driver->{driver_src_dir}."/db";
		my $h = new LkTyH ($db_file);
		if ( $LkTyH::init_status != $LkTyH::TRUE ) {
			die "Fehler LkTyH($db_file)";
		}
		$h->{LkTyH_hash}->{$object} = $db->{DB_TYPE};
		$h = undef;

		# nun muessen ggf. noch abhaengige CIPP-Seiten neu
		# uebersetzt werden

		if ( defined $Driver->{cipp_process_default_db_scripts} ) {
			$messages .= ${CIPP_Depend_Preprocess
				($Driver, $Driver->{project}.".__DEFAULT__", "cipp-db", "db")};
		} elsif ( $db->{DB_TYPE} ne $Driver->{cipp_old_db_type} ) {
			$messages .= ${CIPP_Depend_Preprocess
				($Driver, $object, "cipp-db", "db")};
		}

	}

	return \$messages;
}

sub DB_Delete {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#

	my ($Driver) = @_;

	my $object = $Driver->{object};

	my $db_file = $Driver->{driver_src_dir}."/db";
	my $h = new LkTyH ($db_file);
	if ( $LkTyH::init_status != $LkTyH::TRUE ) {
		die "Fehler LkTyH($db_file)";
	}
	delete $h->{LkTyH_hash}->{$object};
	$h = undef;

	my $default_db = DB_Get_Default($Driver);
	DB_Set_Default ($Driver,'') if $default_db eq $object;
}

sub DB_Get_Default {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	1. Default-DB als String
#
	my ($Driver) = @_;

	my $file = $Driver->{driver_src_dir}."/defaultdb";
	return '' if ! -e $file;

	open (CIPP_DEFAULT_DB, $file) or die "open($file)";
	my $default_db = <CIPP_DEFAULT_DB>;
	close (CIPP_DEFAULT_DB);
	chop $default_db;

	return undef if $default_db eq '';
	return $default_db;
}

sub DB_Set_Default {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. Default-DB als String
#
# OUTPUT:	-
#
	my ($Driver, $default_db) = @_;

	open (CIPP_DEFAULT_DB, ">".$Driver->{driver_src_dir}."/defaultdb")
		or die "open(".$Driver->{driver_src_dir}."/defaultdb)";
	print CIPP_DEFAULT_DB $default_db,"\n";
	close (CIPP_DEFAULT_DB);
}

#------------------------------------------------------------------------------
# Routinen fuer SQL-Objekttyp: cipp-sql
#	SQL_Editor()
#	SQL_Properties()
#	SQL_Prepare_Execute()
#	SQL_Execute()
#------------------------------------------------------------------------------

sub SQL_Editor {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#	      [ 2. Referenz auf Inhalt ]
#	      [ 3. onLoad Tag ]
#
# OUTPUT:	-
#
	my ($Driver, $content, $onload) = @_;

	if ( ! defined $content ) {
		my $content_buffer = '';
		my $filehandle = $Driver->{filehandle};
		while (<$filehandle>) {
			$content_buffer .= $_;
		}
		close $filehandle;
		$content = \$content_buffer;
	}

	$Driver->HTML_Text_Escape ($content);

	if ( $Driver->{event} ne 'show_version' ) {
		$Driver->Print_HTTP_Header();
		$Driver->Print_HTML_Header($onload);
		$Driver->Print_Editor_Header();
	}

	my $font = $Driver->{font};
	my $foo = $USER::Textarea_Cols < $USER::Textarea_Rows;	# sonst Warning

	my $editor_rows = $USER::Textarea_Rows - 10;
	my $execute_rows = 8;
	my $sql_db = $Driver->{header}->Get_Tag ("SQL_DB");

	$sql_db =~ s/^[^\.]+//;		# Projektanteil rausschneiden
	$sql_db = $Driver->{project}.$sql_db;	# aktuelles Projekt davorstellen

	my $quick_execute_source = $Driver->{query}->param('quick_execute_source');

	
	print <<__HTML_CODE;
	<TEXTAREA NAME=source COLS=$USER::Textarea_Cols ROWS=$editor_rows
	 >$$content</TEXTAREA>
__HTML_CODE
	if ( $Driver->{event} ne 'show_version' ) {
		print <<__HTML_CODE;
	<INPUT TYPE=HIDDEN NAME=ausfuehren VALUE="">
        <DIV ALIGN=RIGHT>
	${font}
__HTML_CODE
		if ( not $Driver->{lock_info} ) {
			print <<__HTML_CODE;
        <INPUT TYPE=BUTTON VALUE=" Speichern und Ausführen "
		      onClick="this.form.ausfuehren.value='all'; this.form.submit();">
__HTML_CODE
		}
		print <<__HTML_CODE;
        <P ALIGN=LEFT>SQL-Quick-Execute:</FONT>
	<DIV ALIGN=LEFT>
	<TEXTAREA NAME=quick_execute_source COLS=$USER::Textarea_Cols
	 ROWS=$execute_rows>$quick_execute_source</TEXTAREA>
        <DIV ALIGN=RIGHT>
        ${font}
	<INPUT TYPE=HIDDEN NAME=sql_db VALUE="$sql_db">
__HTML_CODE
		if ( not $Driver->{lock_info} ) {
			print <<__HTML_CODE;
        <INPUT TYPE=BUTTON VALUE=" Speichern und Ausführen "
               onClick="this.form.ausfuehren.value='quick'; this.form.submit();">
__HTML_CODE
		}
		print <<__HTML_CODE;
        </FONT>
	<DIV ALIGN=LEFT>
__HTML_CODE
	}

	if ( $Driver->{event} ne 'show_version' ) {
		$Driver->Print_Editor_Footer();
		$Driver->Print_HTML_Footer();
	}
}

sub SQL_Properties {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. ausgewaehlte Datenbank
#
# OUTPUT:	-
#
	my ($Driver, $sql_db) = @_;
    
	# Liste der vorhandenen Datenbanken aus CIPP-Tied-Hash holen

	my $db_file = $Driver->{driver_src_dir}."/db";
	my $h = new LkTyH ($db_file);
	if ( $LkTyH::init_status != $LkTyH::TRUE ) {
		die "Fehler LkTyH($db_file)";
	}
		
	my @db = sort keys %{$h->{LkTyH_hash}};
#	print STDERR join(", ",@db), " sql_db=$sql_db\n";

	$h = undef;

	my $sql_db_popup;
	if ( scalar (@db) ) {
	 	$sql_db_popup = CGI::popup_menu (
		"-name" => 'cipp_sql_db',
		"-values" => \@db,
		"-default" => $sql_db);
	} else {
		$sql_db_popup = "Es ist noch keine Datenbank definiert!";
	}

#	print STDERR $sql_db_popup, "\n";

	my $font = $Driver->{font};

	print <<__HTML_CODE;
	<P>
	<TABLE BGCOLOR=$USER::Table_Color BORDER=1>
	<TR><TD VALIGN=TOP>
	<TABLE>
	<TR><TD>
	<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
	Datenbank:
	</FONT>
	</TD><TD VALIGN=TOP>
	<FONT FACE=$USER::Font SIZE=$USER::Font_Size>
	$sql_db_popup
	</FONT>
	</TD></TR>
	</TABLE>
	</TD></TR>
	</TABLE>
__HTML_CODE
}

sub SQL_Prepare_Execute {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#	      [ 2. Referenz auf Inhalt ]
#
# OUTPUT:	1. onLoad Tag fuer Editorseite um SQL-Ausfuehrung zu triggern
#

	my ($Driver, $content) = @_;
	my $q = $Driver->{query};

	my $execute = $q->param('ausfuehren');

	return undef if ! $execute;

	# Nun schreiben wir den auszufuehrenden SQL-Code in eine temp. Datei.
	# Ueber onLoad wird driver.pl dann nochmal aufgerufen, um den SQL-Code
	# dann schließlich auszufuehren und die Ausgabe in ein eigenes Fenster
	# umzuleiten

	my $tmpfile = "$IDE::OS_temp_dir/sqlexec$$";
	open (TMP, "> $tmpfile") or die "> $tmpfile";

	my $sql;

	if ( $execute eq 'all' ) {
		$sql = $$content;
	} elsif ( $execute eq 'quick' ) {
		$sql = $q->param('quick_execute_source');
	}

	# Kommentare rausfiltern
#	$sql =~ s/^#.*\n$//;
#	$sql =~ s/\n#.*\n/\n/g;
	$sql =~ s/#.*\n//g;

	print TMP $sql;
	close TMP;

	my $sql_db = $q->param('sql_db');

	my $driver_url = $Driver->{url}."?".$Driver->{driver_parameter_url}.
			 "&event=exec_sql&file=$tmpfile&sql_db=$sql_db";

	my $onload = "sql_window=open('$driver_url','CIPP_SQL_OUTPUT',
          'scrollbars=yes,width=600,height=400,resizable=yes');".
	  "sql_window.focus();";

	return $onload;
}

sub SQL_Execute {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#	      [ 2. Referenz auf Inhalt ]
#
# OUTPUT:	1. onLoad Tag fuer Editorseite um SQL-Ausfuehrung zu triggern
#

	my ($Driver, $content) = @_;
	my $q = $Driver->{query};

	my $object = $Driver->{object};

	my $filename = $q->param('file');

	# haben wir Quick-SQL ohne Speichern?

	if ( $q->param('ausfuehren') eq 'quick_no_save' ) {
		$filename = "$IDE::OS_temp_dir/sqlexec$$";
		open (TMP, "> $filename") or die "> $filename";
		print TMP $q->param('quick_execute_source');
		close TMP;
	}

	my $font = $Driver->{font};

	$Driver->Print_HTTP_Header();
	$Driver->Print_HTML_Header
		(undef, "Ausgabe der SQL-Befehle");

	# Zunaechst mal rauskriegen, mit welchem Befehl wir bei dieser
	# Datenbank arbeiten muessen, sowie welche Environmentvariablen
	# gesetzt sein muessen

	my $sql_db = $q->param('sql_db');

	if ( $sql_db eq '' ) {
		print "$font<B>Derzeit ist diesem SQL-Script keine ",
		      "Datenbank zugewiesen!</B></FONT>";
		$Driver->Print_HTML_Footer();
		return;
	}

	my $header = $Driver->Get_IDE_Header ($sql_db, 'cipp-db');
	if ( ! defined $header ) {
		print "$font<B>Das zugewiesene Datenbankobjekt '$sql_db'".
		      "exisitiert nicht mehr!</B></FONT>";
		$Driver->Print_HTML_Footer();
		return;
	}

	my $href = Scalar2Hash (\$header->{IDE_OBJECT_CONTENT});
	my $message = DB_Parse_ENV ($href);

	if ( $message ) {
		print "$font<B>Das zugewiesene Datenbankobjekt '$sql_db'".
		      "hat einen Syntaxfehler bei den Umgebungsvariablen</B></FONT>";
		$Driver->Print_HTML_Footer();
		return;
	}

	my ($k,$v);
	while ( ($k,$v) = each %{$href->{DB_ENV_HASH}} ) {
		$main::ENV{$k} = $v;
	}

	# Nun wird der SQL-Code über sep.pl ausgeführt
	# Das Parameter-Hash kann schon fast so wie es ist als Input
	# für das SEP genommen werden...

	if ( $href->{DB_TYPE} eq 'CIPP_DB_DBI' or
	     $href->{DB_TYPE} eq 'CIPP_DB_DBI_old' ) {
		$href->{DB_SOURCE} =~ /^dbi:([^:]+)/;
		$href->{DB_TYPE} = $1;
	} else {
		$href->{DB_TYPE} =~ s/^CIPP_DB_//;
	}

	my $sep_cmd = $href->{DB_SEP} || $IDE::SEP_Command;

	delete $href->{DB_SOURCE};
	delete $href->{DB_SEP};
	delete $href->{DB_ENV};
	delete $href->{DB_ENV_HASH};
	delete $href->{DB_AUTOCOMMIT};
	$href->{DB_PASS} =~ s/%(..)/chr(ord(pack('C', hex($1)))^85)/eg;
	$href->{SQL_FILE} = $filename;
	$href->{OUTPUT_FILE} = "$IDE::OS_temp_dir/sep_output$$";

	# nun müssen wir das noch als Scalar haben...

	my $sep_in = Hash2Scalar ($href);

	# ... und schieben den ganzen Rotz ins SEP hinein...

#	print STDERR "$0: sep starten\n";
	
	$ENV{SEP_INPUT} = $$sep_in;
	$sep_cmd = "$Config{perlpath} $sep_cmd";
	my $sep_fetch = `$sep_cmd`;

	# ... und machen daraus wieder ein Hash

	my $sep_out = Scalar2Hash (\$sep_fetch);

#	print "<pre>sep_fetch='$sep_fetch'</pre><P>\n";
#	use Data::Dumper;
#	print "<pre>sep_out=",Dumper($sep_out),"</pre>\n";

	# Fehlernummern nach SEP B-0.5

	my $errmsg = {
		1	=>	"Syntaxfehler bei der Parameterübergabe",
		2	=>	"Es wurden folgende unbekannte Parameter übergeben:",
		3	=>	"Es fehlen folgende Parameter:",
		4	=>	"Dieser Datenbanktyp wird von diesem SEP nicht".
				" unterstützt",
		5	=>	"SQL Datei wurde nicht gefunden!<P>".
				"<B>Hinweis</B>: Sie können keinen Reload auf ".
				"dieses Fenster durchführen!",
		6	=>	"Ausgabedatei konnte nicht geschrieben werden",
		100	=>	"SQL Command Line Monitor wurde nicht gefunden",
		101	=>	"SQL Command Line Monitor ist nicht ausführbar"
	};

	# Ausgabe des Ergebnisses bzw. der Fehlermeldung

	my $msg;
	if ( ! defined $sep_out ) {
		$msg = "Allgemeiner Fehler beim Aufruf von $sep_cmd".
		       "<P><HR><P>";
	} elsif ( $sep_out->{success} eq "no" ) {
		$msg =	"<B>Fehler beim Aufruf des SQL Execution Program (SEP)!</B><P>".
			$errmsg->{$sep_out->{errno}}."<P>".
			$sep_out->{errmsg}."<P>\n";
	}

	print <<__HTML;
	<FORM><TABLE BGCOLOR=$USER::Table_Color BORDER=1 WIDTH=98%>
	<TR><TD>
	<TABLE BORDER=0 WIDTH=100%><TR><TD>$font<B>SQL-Interpreter-Ausgabe von: $object</B></TD>
	<TD ALIGN=RIGHT>$font
	<INPUT TYPE=BUTTON VALUE=" Fenster schließen " onClick="window.close()"></TD>
	</TR></TABLE></TD></TR></TABLE></FORM>
	$font$msg</FONT>
__HTML

#	print $debug;

	if ( -f $href->{OUTPUT_FILE} ) {
		print "<PRE>\n";
		open (OUTPUT, $href->{OUTPUT_FILE});
		while (<OUTPUT>) {
			print;
		}
		close OUTPUT;
		print "</PRE>\n";
	}
	
	unlink $filename;
	unlink $href->{OUTPUT_FILE};

	$Driver->Print_HTML_Footer();
}

#------------------------------------------------------------------------------
# Routinen fuer Konfigurations-Objekttyp: cipp-driver-config
#	Driver_Config_Editor()
#	Driver_Config_Save()
#	Driver_Config_Install()
#------------------------------------------------------------------------------

sub Driver_Config_Editor {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#	      [ 2. Referenz auf Inhalt ]
#	      [ 3. Referenz auf Messages ]
#
# OUTPUT:	-
#
	my ($Driver, $content, $messages) = @_;

	my $object = $Driver->{object};
	if ( $Driver->{event} ne 'show_version' ) {
		$Driver->Print_HTTP_Header();
		$Driver->Print_HTML_Header();
		$Driver->Print_Editor_Header();
	}

	# ggf. Inhalt von Objektdatei einlesen

	if ( ! defined $content ) {
		my $content_buffer = '';
		my $filehandle = $Driver->{filehandle};
		while (<$filehandle>) {
			s/\r//;
			$content_buffer .= $_;
		}
		close ($filehandle);
		$content = \$content_buffer;
	}

	# Inhalt nach Hash konvertieren
	my $conf = Scalar2Hash ($content);

	# Default-Werte setzen
	my $cipp_error_text = $conf->{cipp_error_text};
	if ( $cipp_error_text eq '' ) {
		$cipp_error_text = "Es ist ein interner Fehler aufgetreten! ".
				   "Bitte kontaktieren Sie den Webmaster!";
	}

	if ( ! defined $conf->{cipp_error_show} ) {
		$conf->{cipp_error_show} = 1;
	}

	$Driver->HTML_Text_Escape (\$cipp_error_text);

	# Checkbox für show_error bauen
	my $show_error_checkbox;
	if ( $conf->{cipp_error_show} == 1 ) {
		$show_error_checkbox =
			"<INPUT TYPE=CHECKBOX NAME=cipp_error_show CHECKED>";
	} else {
		$show_error_checkbox =
			"<INPUT TYPE=CHECKBOX NAME=cipp_error_show>";
	}

	# $cipp_cgi_dir, $cipp_img_dir, $cipp_log_file generieren
	my $cipp_cgi_dir = $Driver->{project_dir}."/prod/cgi-bin";
	my $cipp_doc_dir = $Driver->{project_dir}."/prod/htdocs";
	my $cipp_log_file = $Driver->{project_dir}."/prod/logs/cipp.log";

	# Formular ausgeben
	my $font = $Driver->{font};
	print <<__HTML_CODE;
	<P>
	<TABLE BGCOLOR="$USER::Table_Color" BORDER=1 CELLPADDING=5>
	<TR><TD>
	  ${font}URL für CGI-Programme:
	  </FONT>
	</TD><TD>
	  ${font}
	  <INPUT TYPE=TEXT NAME=cipp_cgi_url SIZE=40
		 VALUE="$conf->{cipp_cgi_url}"><BR>Verzeichnis: $cipp_cgi_dir
	</TD></TR>
	<TR><TD>
	  ${font}URL für Dokumente:
	  </FONT>
	</TD><TD>
	  ${font}
	  <INPUT TYPE=TEXT NAME=cipp_doc_url SIZE=40
		 VALUE="$conf->{cipp_doc_url}"><BR>Verzeichnis: $cipp_doc_dir
	</TD></TR>
	<TR><TD>
	  ${font}Verhalten im Fehlerfall:
	  </FONT>
	</TD><TD>
	  ${font}
	  $show_error_checkbox Meldungen auf Browser ausgeben
	</TD></TR>
	<TR><TD VALIGN=TOP>
	  ${font}Fehlermeldung:
	  </FONT>
	</TD><TD>
	  ${font}
	  <TEXTAREA NAME=cipp_error_text
		    COLS=60 ROWS=6>$cipp_error_text</TEXTAREA>
	</TD></TR>
	<TR><TD>
	  ${font}Dateiname des CIPP-Logfiles:
	  </FONT>
	</TD><TD>
	  ${font}
	  $cipp_log_file
	</TD></TR>
	</TABLE>
__HTML_CODE
	if ( $Driver->{event} ne 'show_version' ) {
		Print_Messages($Driver, $messages);
		$Driver->Print_Editor_Footer();
		$Driver->Print_HTML_Footer();
	}
}


sub Driver_Config_Save {
#
# INPUT:	1. Referenz auf das Driver-Objekt
# 
# OUTPUT:	-
#
	my ($Driver) = @_;

	my $object = $Driver->{object};

	my $source = 'Konfiguration';
	my $driver_tags = $Driver->Get_Driver_Tags();
	my $q = $Driver->{query};

	my %conf;
	$conf{cipp_cgi_url}    = $q->param('cipp_cgi_url');
	$conf{cipp_doc_url}    = $q->param('cipp_doc_url');
	$conf{cipp_error_show} = $q->param('cipp_error_show') eq 'on' ? 1 : 0;
	$conf{cipp_error_text} = $q->param('cipp_error_text');

	my $content = Hash2Scalar(\%conf);

	$Driver->Prepare_Save ();
	$Driver->Put_Driver_Tags ($driver_tags);

	my $object_path = $Driver->{object_path};
	open (CONFIG_SAVE, "> $object_path") or
		die "SAVE: > $object_path";
	$Driver->{header}->Write_IDE_Header ( *CONFIG_SAVE );
	print CONFIG_SAVE $$content, "\n";
	close CONFIG_SAVE;

	return $content;
}


sub Driver_Config_Install {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. Rerefenz auf den Inhalt
#
# OUTPUT:	1. Messages
#
	my ($Driver, $content) = @_;

	my $conf = Scalar2Hash ($content);
	my $config_file = $Driver->{project_dir}."/prod/config/cipp.conf";

	my $cipp_cgi_dir = $Driver->{project_dir}."/prod/cgi-bin";
	my $cipp_doc_dir = $Driver->{project_dir}."/prod/htdocs";
	my $cipp_log_file = $Driver->{project_dir}."/prod/logs/cipp.log";

	open (CIPP_CONFIG, "> $config_file") or die "open: $config_file";
	print CIPP_CONFIG q{package CIPP_Exec;},"\n";
	print CIPP_CONFIG q{$cipp_project = '},$Driver->{project},q{';},"\n";
	print CIPP_CONFIG q{$cipp_cgi_url = '},$conf->{cipp_cgi_url},q{';},"\n";
	print CIPP_CONFIG q{$cipp_doc_url = '},$conf->{cipp_doc_url},q{';},"\n";
	print CIPP_CONFIG q{$cipp_cgi_dir = '},$cipp_cgi_dir,q{';},"\n";
	print CIPP_CONFIG q{$cipp_doc_dir = '},$cipp_doc_dir,q{';},"\n";
	print CIPP_CONFIG q{$cipp_log_file = '},$cipp_log_file,q{';},"\n";
	print CIPP_CONFIG q{$cipp_error_show = },$conf->{cipp_error_show},";\n";
	print CIPP_CONFIG q{$cipp_error_text = q[}.$conf->{cipp_error_text},"];\n";
	print CIPP_CONFIG q{$cipp_url = $cipp_cgi_url;},"\n";
	print CIPP_CONFIG "1;\n";
	close (CIPP_CONFIG);

	my $messages = "CIPP-Konfigurationsfile installiert unter\n$config_file";

	return \$messages;
}


# Tools ------------------------------------------------------------------------

sub MkPath {
#
# INPUT:	1. Vollständiger Pfadname
#
# OUTPUT:	-
#
#
	my ($path) = @_;

	if ( ! -d $path ) {
		eval { mkpath $path, 0, 0770; };
		die $@ if $@;
	}
}

sub RmPath {
#
# INPUT:	1. Absoluter Pfadanteil
#		2. relativer, zu löschender, Pfadanteil
#	
# OUTPUT:	-
#
#
	my ($root, $sub) = @_;

#	Logger ("RmPath: root=$root sub=$sub");

	my $path = "$root/$sub";

	DELLOOP: while ( -d $path ) {
		if ( ! rmdir $path ) {
			last DELLOOP;
		} else {
#			Logger ("RmPath deleted: path=$path");
			$path =~ s!/[^/]+$!!;
			last if $path eq $root;
		}
	}

#	Logger ("RmPath finished: path=$path");
}

sub Logger {
	my ($message) = @_;
	return if ! $IDE::OS;

	open (LOGGER, ">> $main::logger_file") or die ">> $main::logger_file";
	print LOGGER scalar(localtime), " $$:\t", $message, "\n";
	close LOGGER;
}



#------------------------------------------------------------------------------
# Routinen zur Projektneuübersetzung
#	Make_All()
#------------------------------------------------------------------------------

sub Make_All {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	-
#
	my ($Driver) = @_;

	Make_All_Delete_CIPP_DB_File ($Driver);

	my $project = $Driver->{project};

	$| = 1;

	my @object_type_order = (
		'cipp-db',
		'cipp-driver-config',
		'cipp-config',
		'cipp-img',
		'cipp',
		'cipp-html'
	);

	my $lref = $Driver->Get_Objects_In_Folder ($project);
	my %objects;

	my ($i, $o, $t);
	foreach $i ( @{$lref} ) {
		($o, $t) = split ("\t", $i);
		push @{$objects{$t}}, $o;
	}
	$i = 0;
	print "<P><B>Übersetze und installiere alle Objekte...</B>\n";
	print "<BLOCKQUOTE>\n";
	
	foreach $t (@object_type_order) {
		my $class = $dep_class{$t};
		$class = 'include' if $t eq 'cipp';
		
		if ( $class ) {
			print "<I>>> Lösche Abhängigkeitsinformationen zu '$class'...</I>\n";
			my $Depend = $Driver->Get_Depend_Object($class);
			$Depend->Clear_Dependencies ();
		}
		foreach $o (@{$objects{$t}}) {
			print "<P>$o...\n";
			my $message = Make_All_Install ($Driver, $o, $t);
			print "<BLOCKQUOTE><PRE>$$message</PRE></BLOCKQUOTE>\n";
			print "<SCRIPT>self.window.scroll(0,5000000)</SCRIPT>\n";
			print "<SCRIPT>self.window.scroll(0,5000000)</SCRIPT>\n";
		}
	}
	print "</BLOCKQUOTE>\n";
	
#	print "<SCRIPT>self.window.scroll(0,5000000)</SCRIPT>\n";
#	print "<SCRIPT>self.window.scroll(0,5000000)</SCRIPT>\n";
}


sub Make_All_Install {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#		2. Objekt
#		3. Objekttyp
#
# OUTPUT:	1. Refernz auf Install-Message
#
	my ($Driver, $object, $object_type) = @_;

	$Driver->Reinit_With_Object ($object, $object_type);

	return CIPP_Preprocess ($Driver) if $object_type eq 'cipp' or
					    $object_type eq 'cipp-html';

	my $fh = $Driver->{filehandle};
	my $content = join '', <$fh>;
	
	if ( $object_type eq 'cipp-db' ) {
		return DB_Install ($Driver, \$content);
	} elsif ( $object_type eq 'cipp-img' ) {
		return Image_Install ($Driver, \$content);
	} elsif ( $object_type eq 'cipp-config' ) {
		return Config_Install ($Driver, \$content);
	} elsif ( $object_type eq 'cipp-driver-config' ) {
		return Driver_Config_Install ($Driver, \$content);
	}

	return \"Objekttyp unbekannt: '$object_type'";
}


sub Make_All_Delete_CIPP_DB_File {
#
# INPUT:	1. Referenz auf das Driver-Objekt
#
# OUTPUT:	1. Referenz auf Message
#
	my ($Driver) = @_;
	return;

	my $dir = $Driver->{driver_src_dir};
	print STDERR "delete: $dir: db.dir db.lock db.pag\n";
	unlink ("$dir/db.dir", "$dir/db.lock", "$dir/db.pag");
}
