FROM ubuntu:14.04

ADD ./ /code/

RUN apt-get update -qq && cat /code/packages.txt | xargs apt-get -yqq install

WORKDIR /code/

ENTRYPOINT ["paver"]

CMD ["run"]