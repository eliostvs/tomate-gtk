#
# spec file for package python-tomate
#
# Copyright (c) 2014 Elio Esteves Duarte <elio.esteves.duarte@gmail.com>
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#

%define real_name tomate
%define module_name %{real_name}_gtk

Name: %{real_name}-gtk
Version: 0.5.0
Release: 0
License: GPL-3.0+
Summary: Tomate Pomodoro Timer (GTK+ Interface)
Source: %{name}-upstream.tar.gz
Url: https://github.com/eliostvs/tomate-gtk

BuildRoot: %{_tmppath}/%{name}-%{version}-build

BuildRequires: python-devel
BuildRequires: python-setuptools

Requires: python-setuptools
Requires: python-tomate >= 0.5.0

%if 0%{?fedora}
Requires: dbus-x11
BuildArch: noarch
Requires: gtk3
%endif

%if 0%{?suse_version}
BuildArchitectures: noarch
BuildRequires: desktop-file-utils
BuildRequires: hicolor-icon-theme
Requires: typelib-1_0-Gtk-3_0
Requires: dbus-1-x11
%endif

%description
Tomate Pomodoro Timer (GTK+ Interface).

%prep
%setup -q -n %{name}-upstream

%build
python setup.py build

%install
python setup.py install --prefix=%{_prefix} --root=%{buildroot}

%post
%if 0%{?suse_version}
%desktop_database_post
%icon_theme_cache_post
%endif
%if 0%{?fedora}
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
%endif

%postun
%if 0%{?suse_version}
%desktop_database_postun
%icon_theme_cache_postun
%endif
%if 0%{?fedora}
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi
%endif

%files
%defattr(-,root,root,-)
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/*/*.*
%{python_sitelib}/*

%doc AUTHORS COPYING README.md

%changelog