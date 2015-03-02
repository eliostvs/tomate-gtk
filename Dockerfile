FROM ubuntu:14.04

RUN apt-get install -y -qq wget

RUN wget -O- http://download.opensuse.org/repositories/home:/eliostvs:/tomate/xUbuntu_14.04/Release.key | apt-key add -
RUN echo 'deb http://download.opensuse.org/repositories/home:/eliostvs:/tomate/xUbuntu_14.04/ ./' > /etc/apt/sources.list.d/tomate.list

COPY ./ /code/

RUN apt-get update -qq && cat /code/packages.txt | xargs apt-get -yqq install

RUN apt-get clean

WORKDIR /code/

ENTRYPOINT ["paver"]

CMD ["run"]