FROM debian

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update

# install bluez related packages
RUN apt-get update && apt-get install -y \
    bluez \
    dbus \
    sudo

RUN apt-get update && apt-get -y install \
    locales \
    python3-pip \
    bluetooth \
    bluez \
    python3-bluez \
    python3-gi \
    libbluetooth-dev \
    python3-dbus \
	kmod \ 
	kbd
	
RUN python3 -m pip install pybluez
RUN pip3 install keyboard

# setup bluetooth permissions
COPY ./bluezuser.conf /etc/dbus-1/system.d/
RUN useradd -m bluezuser \
 && adduser bluezuser sudo \
 && passwd -d bluezuser
USER bluezuser

# setup startup script
COPY entrypoint.sh /entrypoint.sh
RUN echo "//entrypoint.sh" >> /home/bluezuser/.bashrc
