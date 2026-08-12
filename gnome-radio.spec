Name:           gnome-radio
Version:        83.0
Release:        1%{?dist}
Summary:        Radio
License:        GPLv3+
URL:            http://www.gnomeradio.org/
Source:         %{url}/src/%{name}-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  gtk3-devel
BuildRequires:  pango
BuildRequires:  libchamplain-devel
BuildRequires:  libxml2-devel
BuildRequires:  intltool
BuildRequires:  itstool
BuildRequires:  libappstream-glib
BuildRequires:  desktop-file-utils
BuildRequires:  geoclue2-devel
BuildRequires:  geocode-glib-devel
BuildRequires:  gstreamer1-devel
BuildRequires:  gstreamer1-plugins-bad-free-devel
BuildRequires:  gstreamer1-plugins-base-devel
Requires:       gstreamer1 >= 1.8.3
Requires:       gstreamer1-plugins-ugly-free >= 1.8.3
Requires:       geocode-glib >= 3.20.1
Requires:       gtk3 >= 3.24.34
Requires:       geoclue2 >= 2.5.7
Requires:       goocanvas2 >= 2.0.4
Provides:       gnome-internet-radio-locator = 16.0.6
Obsoletes:      gnome-internet-radio-locator < 16.0.6
Provides:       gtk-radio = 550.3
Obsoletes:      gtk-radio < 550.3

%description

Radio is a Free Software program that allows you to easily locate Free
Internet Radio stations by broadcasters on the Internet with the help
of map and text search.

Radio is developed on the GNOME desktop platform.

Radio supports Public Radio (www.npr.org) in USA.

%prep
%setup -q

%build
%configure --with-recording --disable-silent-rules --disable-schemas
%make_build
%install
%make_install
%find_lang %{name} --with-man

%check
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/%{name}.appdata.xml
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{name}.desktop
%files -f %{name}.lang
%doc AUTHORS NEWS README TODO ChangeLog
%license COPYING
%{_bindir}/%{name}
%{_bindir}/gnome-internet-radio-locator
%{_bindir}/gnome-radio-oop
%{_bindir}/gtk-radio
%{_bindir}/gtk-internet-radio-locator
%{_bindir}/org.gnome.Radio
%{_bindir}/radio-beamy
%{_bindir}/radio-icy
%{_datadir}/%{name}/org.gnome.Radio.dtd
%{_datadir}/%{name}/org.gnome.Radio.xml
%{_datadir}/%{name}/doc/AAMOT.txt.xz
%{_datadir}/%{name}/doc/Aamot-2020.txt.xz
%{_datadir}/doc/%{name}/radio.html
%{_datadir}/doc/%{name}/radio-maps.html
%{_datadir}/doc/%{name}/studio.html
%{_datadir}/%{name}/gnome-radio-48.0.dtd
%{_datadir}/%{name}/gnome-radio.xml
%{_metainfodir}/%{name}.appdata.xml
%{_metainfodir}/gtk-radio.appdata.xml
%{_metainfodir}/org.gnome.Radio.appdata.xml
%{_metainfodir}/radio-beamy.appdata.xml
%{_datadir}/applications/%{name}.desktop
%{_datadir}/applications/gtk-radio.desktop
%{_datadir}/applications/org.gnome.Radio.desktop
%{_datadir}/applications/radio-beamy.desktop
%{_datadir}/gtk-radio/gtk-radio-550.3.dtd
%{_datadir}/gtk-radio/gtk-radio.xml
%{_datadir}/gtk-internet-radio-locator/internet-radio-locator-48.0.dtd
%{_datadir}/gtk-internet-radio-locator/internet-radio-locator.xml
%{_datadir}/icons/hicolor/scalable/apps/gnome-radio.svg
%{_datadir}/icons/hicolor/scalable/apps/gtk-radio.svg
%{_datadir}/icons/hicolor/scalable/apps/org.gnome.Radio.svg
%{_datadir}/icons/hicolor/scalable/apps/radio-beamy.svg
%{_mandir}/man1/%{name}.1*

%changelog
* Tue Aug 11 2026 Ole Aamot <ole@aamot.org> - 83.0-1
- Stable gnome-radio 83.0 with NRK P1 Rogaland (Stavanger, Norway)

* Fri Jul 31 2026 Ole Aamot <ole@aamot.org> - 82.0-1
- Stable gnome-radio 82.0 rebuilt from www.gnomeradio.org

* Wed Jul 29 2026 Ole Aamot <ole@aamot.org> - 81.0-1
- Stable gnome-radio 81.0 with C-SPAN, United States of America

* Sun Jul 19 2026 Ole Aamot <ole@aamot.org> - 80.0-1
- Stable gnome-radio 80.0 with World Wide Web Studio

* Sun Jul 05 2026 Ole Aamot <ole@aamot.org> - 79.0-1
- Stable gnome-radio 79.0 with P4 Radio Hele Norge (Norge)

* Mon May 25 2026 Ole Aamot <ole@aamot.org> - 78.0-1
- Stable gnome-radio 78.0 with Radio Vaticana (Vatican City)

* Thu May 07 2026 Ole Aamot <ole@aamot.org> - 77.0-1
- Stable gnome-radio 77.0 with Radio Rana (Mo i Rana, Norge)

* Sun Apr 05 2026 Ole Aamot <ole@aamot.org> - 76.0-1
- Stable gnome-radio 76.0 with ArmyFM (Kyiv, Ukraine) and Radio Wien (Vienna, Austria)

* Fri Mar 20 2026 Ole Aamot <ole@aamot.org> - 75.0-1
- Stable gnome-radio 75.0 with Languages

* Wed Mar 18 2026 Ole Aamot <ole@aamot.org> - 74.0-1
- Stable gnome-radio 74.0 with brand new radio-beamy

* Mon Mar 02 2026 Ole Aamot <ole@aamot.org> - 73.0-1
- Stable gnome-radio 73.0 with SRIB (Bergen, Norway)

* Wed Feb 18 2026 Ole Aamot <ole@aamot.org> - 72.0-1
- Stable gnome-radio 72.0 with Nea Radio (Stjørdal, Norway)

* Mon Feb 16 2026 Ole Aamot <ole@aamot.org> - 71.0-1
- Development gnome-radio 71.0 with Radio Riks (Nesodden, Norway)

* Fri Feb 13 2026 Ole Aamot <ole@aamot.org> - 70.0-1
- Stable gnome-radio 70.0 with Radio Alhara (Betlehem, Palestine)

* Tue Feb 03 2026 Ole Aamot <ole@aamot.org> - 69.0-1
- Stable gnome-radio 69.0 with Radio Stortinget (Stortinget, Oslo, Norway)

* Mon Feb 02 2026 Ole Aamot <ole@aamot.org> - 68.0-1
- Stable gnome-radio 68.0 with Radio Stortinget (Oslo, Norway)

* Sat Jan 31 2026 Ole Aamot <ole@aamot.org> - 67.0-1
- Stable gnome-radio 67.0 with Radio Latin-Amerika (Oslo, Norway)

* Sat Jan 31 2026 Ole Aamot <ole@aamot.org> - 66.0-1
- Stable gnome-radio 66.0 with Radio Cuba (Havana, Cuba)

* Mon Jan 26 2026 Ole Aamot <ole@aamot.org> - 65.0-1
- Stable gnome-radio 65.0 with The Current (Minneapolis, Minnesota, United States of America)

* Sun Jan 25 2026 Ole Aamot <ole@aamot.org> - 64.1-1
- Stable gnome-radio 64.1 with Minnesota Public Radio (Saint Paul, Minnesota, U.S.A.)

* Tue Jan 06 2026 Ole Aamot <ole@aamot.org> - 64.0-1
- Stable gnome-radio 64.0 with Circuito Adulto Joven (Caracas, Venezuela)

* Tue Dec 23 2025 Ole Aamot <ole@aamot.org> - 63.0-1
- Stable gnome-radio 63.0 with Free World Radio (Greenland)

* Mon Dec 08 2025 Ole Aamot <ole@aamot.org> - 62.0-1
- Stable gnome-radio 62.0 with World Wide Talk Radio

* Wed Oct 29 2025 Ole Aamot <ole@aamot.org> - 60.0-1
- Stable gnome-radio 60.0 with World Wide Live Radio

* Wed Oct 15 2025 Ole Aamot <ole@aamot.org> - 59.0-1
- Stable gnome-radio 59.0 with Free Internet Talk Radio (ARPANET)

* Wed Oct 08 2025 Ole Aamot <ole@aamot.org> - 58.0-1
- Stable gnome-radio 58.0 with BBC World Service (World Wide Web)

* Wed Oct 01 2025 Ole Aamot <ole@aamot.org> - 57.0-1
- Stable gnome-radio 57.0 with Radio Norwegian (Norway)

* Fri Sep 12 2025 Ole Aamot <ole@aamot.org> - 56.0-1
- Stable gnome-radio 56.0 with BBC World Service (United Kingdom)

* Wed Sep 10 2025 Ole Aamot <ole@aamot.org> - 52.0-1
- Stable gnome-radio 52.0 with Radio Warszawa (Warszawa, Poland)

* Sun Aug 10 2025 Ole Aamot <ole@aamot.org> - 51.0-1
- Stable gnome-radio 51.0 with Gudbrandsdalsradioen (Vinstra, Norway) and Elverumsradioen (Elverum, Norway)

* Sun Jul 27 2025 Ole Aamot <ole@aamot.org> - 50.2-1
- Stable gnome-radio 50.2 with HamarRadioen for FC43

* Sun Jun 29 2025 Ole Aamot <ole@aamot.org> - 50.1-1
- Initial gnome-radio 50.1 builds on Fedora Linux 43

* Sun Jun 29 2025 Ole Aamot <ole@aamot.org> - 50.0-1
- Initial gnome-radio 50.0 builds on Fedora Linux 42

* Sun Jun 29 2025 Ole Aamot <ole@aamot.org> - 49.2-1
- Development gnome-radio 49.2 with HamarRadioen (Stange, Norge / Hamar, Norge / Ringsaker, Norge)

* Sun Jun 29 2025 Ole Aamot <ole@aamot.org> - 49.1-1
- Development gnome-radio 49.1 with HamarRadioen (Hamar-region, Norge)

* Sun Mar 02 2025 Ole Aamot <ole@aamot.org> - 49.0-1
- Initial gnome-radio 49.0 with Vermont Public Radio (Vermont, United States of America)

* Thu Feb 27 2025 Ole Aamot <ole@aamot.org> - 48.4-1
- Initial gnome-radio 48.4 with Radio 102 (Haugesund, Norway) and Radio Haugaland (Haugaland, Norway)

* Sat Feb 22 2025 Ole Aamot <ole@aamot.org> - 48.3-1
- Initial gnome-radio 48.3 with Free Internet Radio Stations

* Sat Feb 22 2025 Ole Aamot <ole@aamot.org> - 48.20250222-1
- Initial gnome-radio 48.20250222 with Free Radio Stations

* Wed Jan 22 2025 Ole Aamot <ole@aamot.org> - 48.20250122-1
- Initial gnome-radio 48.20250122 with Radio Folgefonn (Norway)

* Mon Jan 20 2025 Ole Aamot <ole@aamot.org> - 48.20250120-1
- Initial gnome-radio 48.20250120 with npr.org (United States of America)

* Wed Dec 25 2024 Ole Aamot <ole@aamot.org> - 48.1-1
- Initial gnome-radio 48.1 build with hi, is, ka, ru

* Sun Nov 03 2024 Ole Aamot <ole@aamot.org> - 48.0-1
- Initial gnome-radio 48.0 build with BBC (United Kingdom) and NRK (Norway)

* Sun Sep 25 2022 Ole Aamot <ole@gnome.org> - 47.0-1
- Initial gnome-radio 47.0 build with RBB (Frankfurt am Main, Germany)

* Mon Sep 19 2022 Ole Aamot <ole@gnome.org> - 46.0-1
- Initial gnome-radio 46.0 build with KXSC (LA, USA)

* Mon Sep 19 2022 Ole Aamot <ole@gnome.org> - 45.3-1
- Initial gnome-radio 45.3 builds with GtkEntry icon

* Sun Sep 18 2022 Ole Aamot <ole@gnome.org> - 45.2-1
- Initial gnome-radio 45.2 builds with libtool 2.4.7

* Sun Aug 14 2022 Ole Aamot <ole@gnome.org> - 45.1-1
- Initial gnome-radio 45.1 builds with Free Asia radio

* Wed Jul 20 2022 Ole Aamot <ole@gnome.org> - 45.0-1
- Initial gnome-radio 45.0 builds with GTK on Fedora 36

* Fri May 27 2022 Ole Aamot <ole@gnome.org> - 16.0.43-1
- Initial gnome-radio 16.0.43 builds on Fedora Linux 36

* Sat Apr 02 2022 Ole Aamot <ole@gnome.org> - 16.0.42-1
- Second gnome-radio 16.0.42 builds on Fedora Linux 36

* Mon Mar 28 2022 Ole Aamot <ole@gnome.org> - 16.0.6-1
- Initial gnome-radio 16.0.6 builds on Fedora Linux 36

* Mon Mar 28 2022 Ole Aamot <ole@gnome.org> - 16.0.5-1
- Initial gnome-radio 16.0.5 builds on Fedora Linux 35

* Sat Mar 19 2022 Ole Aamot <ole@gnome.org> - 16.0.4-1
- Initial gnome-radio 16.0.4 builds on Fedora Linux 36

* Tue Mar 15 2022 Ole Aamot <ole@gnome.org> - 14.0.1-1
- Initial gnome-radio 14.0.1 builds on Fedora Linux 35
