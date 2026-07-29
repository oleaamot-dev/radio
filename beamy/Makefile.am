AM_CPPFLAGS = $(GNOME_RADIO_CFLAGS) \
	-DGTK4_GNOME_RADIO_DATADIR="\"$(pkgdatadir)\"" \
	-DGTK4_GNOME_RADIO_LOCALEDIR="\"$(localedir)\""

AM_CFLAGS = $(GNOME_RADIO_CFLAGS) \
	-DGTK4_GNOME_RADIO_DATADIR="\"$(pkgdatadir)\"" \
	-DGTK4_GNOME_RADIO_LOCALEDIR="\"$(localedir)\""
	$(NULL)

AM_LDFLAGS= $(GTK4_GNOME_RADIO_LIBS) 

bin_PROGRAMS = radio-beamy

radio_beamy_SOURCES = \
		radio-beamy.c

radio_beamy_CFLAGS  = $(GNOME_RADIO_CFLAGS) \
	       -DDATADIR=\"$(datadir)\" \
	       -DGTK4_GNOME_RADIO_DEBUG=1 \
	       -DGTK4_GNOME_RADIO_CFG \
               -DGTK4_GNOME_RADIO_LOCALEDIR="\"$(localedir)\""

radio_beamy_LDADD = $(GNOME_RADIO_LIBS)

radio_beamydir = $(datadir)/gnome-radio

LDADD = $(GNOME_RADIO_LIBS)
