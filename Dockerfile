FROM ubuntu:14.04

ENV PROJECT /code/

RUN apt-get update -qq && apt-get install -yq \
    dbus-x11 \
    make \
    gir1.2-appindicator3-0.1 \
    gir1.2-gdkpixbuf-2.0 \
    gir1.2-glib-2.0 \
    gir1.2-gtk-3.0 \
    python-blinker \
    python-coverage \
    python-dbus \
    python-enum34 \
    python-gi \
    python-mock \
    python-nose \
    python-xdg \
    python-yapsy \
    xvfb \
    wget

RUN wget -O- http://download.opensuse.org/repositories/home:/eliostvs:/tomate/xUbuntu_14.04/Release.key | apt-key add -
RUN echo 'deb http://download.opensuse.org/repositories/home:/eliostvs:/tomate/xUbuntu_14.04/ ./' > /etc/apt/sources.list.d/tomate.list

RUN apt-get update -qq && apt-get install -yq python-wiring python-wrapt

RUN apt-get clean

COPY . $PROJECT
WORKDIR $PROJECT

ENTRYPOINT ["make"]
CMD ["test"]