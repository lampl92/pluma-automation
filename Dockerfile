FROM ubuntu:18.04

# Copy farm core
COPY ./ /root/farm-core

RUN apt-get update && apt-get install -y python3

# Install farm core
RUN /root/farm-core/install.sh -n
