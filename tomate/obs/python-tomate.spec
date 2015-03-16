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

Name: python-%{real_name}
Version: 0.2.2
Release: 0
License: GPL-3.0+
Source: %{real_name}-upstream.tar.gz
Url: https://github.com/eliostvs/tomate
Summary: A pomodoro timer

BuildRoot: %{_tmppath}/%{name}-%{version}-build

BuildRequires: python-devel
BuildRequires: python-setuptools

Requires: python-blinker
Requires: python-enum34
Requires: python-six
Requires: python-wiring
Requires: python-wrapt

%if 0%{?fedora}
BuildArch: noarch
Requires: dbus-python
Requires: pygobject3
Requires: python-yapsy
Requires: pyxdg
%endif

%if 0%{?suse_version}
BuildArchitectures: noarch
Requires: dbus-1-python
Requires: python-gobject
Requires: python-xdg
Requires: python-Yapsy
%endif

%description
A pomodoro timer. Core classes.

%prep
%setup -q -n %{real_name}-upstream

%build
python setup.py build

%install
python setup.py install --prefix=%{_prefix} --root=%{buildroot}

%files
%defattr(-,root,root,-)
%{python_sitelib}/*

%doc AUTHORS COPYING README.md

%changelog