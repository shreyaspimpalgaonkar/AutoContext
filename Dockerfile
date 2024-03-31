# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Set environment variables to avoid user interaction during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.12, pip, and other necessary packages
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.12 python3.12-distutils python3.12-venv curl && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 && \
    python3.12 -m pip install --upgrade pip

# Install Git
RUN apt-get update && apt-get install -y git
RUN apt-get install -y vim

# Copy your project to the container
RUN ls -la
WORKDIR /opt/rtr_app 
RUN pwd
RUN ls -la
COPY ./requirements.txt /opt/rtr_app/requirements.txt
RUN ls -la
RUN pip install -r requirements.txt
