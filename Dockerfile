FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -qq && apt-get install -y \
    dbus-x11 \
    gir1.2-appindicator3-0.1 \
    gir1.2-gdkpixbuf-2.0 \
    gir1.2-glib-2.0 \
    gir1.2-gstreamer-1.0 \
    gir1.2-gtk-3.0 \
    gir1.2-gtk-3.0 \
    gir1.2-notify-0.7 \
    gir1.2-playerctl-2.0 \
    gir1.2-unity-5.0 \
    git \
    gstreamer1.0-plugins-base \
    make \
    notification-daemon \
    python3-blinker \
    python3-dbus \
    python3-dbusmock \
    python3-gi \
    python3-pip \
    python3-pytest \
    python3-pytest-cov \
    python3-pytest-flake8 \
    python3-pytest-mock \
    python3-venusian \
    python3-wrapt \
    python3-xdg \
    python3-yapsy \
    xvfb

RUN pip3 install \
    black \
    isort \
    ruff \
    git+https://git@github.com/eliostvs/wiring.git@master

WORKDIR /code

ENTRYPOINT ["make"]

CMD ["test"]
