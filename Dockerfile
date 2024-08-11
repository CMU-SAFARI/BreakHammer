FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    build-essential \
    g++-10 \
    wget \
    curl \
    git \
    cmake \
    python3 \
    python3-pip

COPY . /app

WORKDIR /app

RUN pip3 install matplotlib pandas seaborn pyyaml wget scipy

ENTRYPOINT ["/bin/bash"]