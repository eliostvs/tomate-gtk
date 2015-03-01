FROM ubuntu:14.04

RUN echo 'Acquire::http::Proxy "http://172.17.42.1:3142";' > /etc/apt/apt.conf.d/90-apt-cacher.conf

RUN apt-get update -qq && apt-get install -y wget

RUN wget -O- http://download.opensuse.org/repositories/home:/eliostvs:/wrapt/xUbuntu_14.04/Release.key | apt-key add -
RUN echo 'deb http://download.opensuse.org/repositories/home:/eliostvs:/wrapt/xUbuntu_14.04/ ./' >> /etc/apt/sources.list
RUN wget -O- http://download.opensuse.org/repositories/home:/eliostvs:/wiring/xUbuntu_14.04/Release.key | apt-key add -
RUN echo 'deb http://download.opensuse.org/repositories/home:/eliostvs:/wiring/xUbuntu_14.04/ ./' >> /etc/apt/sources.list

ADD ./ /code/

RUN apt-get update -qq && cat /code/packages.txt | xargs apt-get -yqq install

RUN pip install -e git+https://github.com/msiedlarek/wiring#egg=wiring

RUN apt-get clean

WORKDIR /code/

ENTRYPOINT ["paver"]

CMD ["run"]