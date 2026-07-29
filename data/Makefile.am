SUBDIRS = icons

@INTLTOOL_DESKTOP_RULE@

DESKTOP_IN_FILES= gnome-radio.desktop.in.in gtk-radio.desktop.in.in org.gnome.Radio.desktop.in.in radio-beamy.desktop.in.in
DESKTOP_FILES= $(DESKTOP_IN_FILES:.desktop.in.in=.desktop)

desktopdir = $(datadir)/applications
desktop_DATA = $(DESKTOP_FILES)

@INTLTOOL_XML_RULE@
appdatadir = $(datadir)/metainfo
appdata_in_files = gnome-radio.appdata.xml.in gtk-radio.appdata.xml.in org.gnome.Radio.appdata.xml.in radio-beamy.appdata.xml.in
appdata_DATA = $(appdata_in_files:.xml.in=.xml)

EXTRA_DIST = $(DESKTOP_IN_FILES) $(DESKTOP_FILES) $(appdata_in_files)

CLEANFILES = $(appdata_DATA)

DISTCLEANFILES = $(DESKTOP_FILES)

-include $(top_srcdir)/git.mk
