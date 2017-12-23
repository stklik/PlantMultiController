FROM resin/rpi-raspbian:stretch

MAINTAINER "Stefan Klikovits" <stefan@klikovits.net>

# install git
RUN apt-get update -y && \
    apt-get install -y git python3

# get PMC from github
RUN git clone https://github.com/stklik/PlantMultiController.git
WORKDIR /PlantMultiController

# install dependencies
RUN pip3 install -r requirements.txt

# get Chirp
RUN git submodule init && \
    git submodule update

# run server
CMD python3 startup.py
