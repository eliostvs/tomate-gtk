FROM eliostvs/tomate

ENV PROJECT /code/

RUN apt-get update -qq && apt-get install -yq \
    dbus-x11 \
    make \
    gir1.2-appindicator3-0.1 \
    gir1.2-gdkpixbuf-2.0 \
    gir1.2-gtk-3.0 \
    wget

RUN apt-get clean

COPY . $PROJECT
WORKDIR $PROJECT

ENTRYPOINT ["make"]
CMD ["test"]