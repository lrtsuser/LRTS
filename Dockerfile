# Use the official Ubuntu 20.04 as a base image
FROM ubuntu:20.04

# Set environment variables to avoid user interaction during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install necessary packages including Python
RUN apt-get update && \
    apt-get install -y \
    software-properties-common \
    wget \
    curl \
    git \
    vim \
    emacs \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3.9 \
    python3.9-dev \
    python3.9-venv \
    python3-pip \
    rm -rf /var/lib/apt/lists/*

# Remove existing symbolic links and create new ones for python3.9 as python3 and python3 as python
RUN rm /usr/bin/python3 && \
    ln -s /usr/bin/python3.9 /usr/bin/python3 && \
    ln -s /usr/bin/python3 /usr/bin/python

# Upgrade pip and install common Python packages
RUN pip3 install --upgrade pip && \
    pip3 install \
    numpy \
    pandas \
    scipy \
    matplotlib \
    jupyter \
    flask \
    django

# Set the working directory
WORKDIR /app

# Copy the application code to the container
COPY . /app

# Install the Python packages from requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR /app/artifact

CMD ["bash"]
