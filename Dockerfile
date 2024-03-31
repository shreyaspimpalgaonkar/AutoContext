# Use python 3.12 as the base image
FROM python:3.12

# Set environment variables to avoid user interaction during installation
ENV DEBIAN_FRONTEND=noninteractive

# Copy your project to the container
WORKDIR /opt/rtr_app 
COPY ./requirements.txt /opt/rtr_app/requirements.txt
RUN pip install -r requirements.txt
