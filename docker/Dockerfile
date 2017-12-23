FROM resin/rpi-raspbian:stretch

MAINTAINER "Stefan Klikovits" <stefan@klikovits.net>

# install git
RUN apt-get update -y && \
    apt-get install -y \
        git \
        libusb-1.0-0 \
        python3 \
        python3-pip \
        python3-setuptools \
        python-smbus

# get PMC from github
RUN git clone https://github.com/stklik/PlantMultiController.git
WORKDIR /PlantMultiController

# install dependencies
RUN pip3 install wheel
RUN pip3 install -r requirements.txt

# get Chirp
RUN git submodule init && \
    git submodule update

RUN touch /etc/udev/rules.d/99-yoctopuce-all.rules
RUN echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"24e0\", MODE=\"0666\"" >> \
    /etc/udev/rules.d/99-yoctopuce-all.rules

RUN cat /etc/udev/rules.d/99-yoctopuce-all.rules

# run server
CMD python3 startup.py
