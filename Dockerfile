# FROM ubuntu:latest

# RUN apt-get update
# RUN apt-get install -y git
# RUN apt-get install -y wget

# ARG DEBIAN_FRONTEND=noninteractive
# RUN apt-get -y update && apt-get install -y --no-install-recommends nginx

# RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# RUN bash Miniconda3-latest-Linux-x86_64.sh -b -p /miniconda
# ENV PATH=/miniconda/bin:$PATH

# # PACKAGES to install
# RUN conda install -y -c anaconda boto3 gunicorn gevent flask
# RUN conda install -y -c conda-forge pandas numpy requests
# RUN pip install justext

# # environment variables?
# ENV PYTHONUNBUFFERED=TRUE
# ENV PYTHONDONTWRITEBYTECODE=TRUE
# ENV PATH="/opt/program:${PATH}"
# ENV MODEL_PATH="/opt/ml/model"
# ENV SAGEMAKER_MODEL_SERVER_TIMEOUT=1200

# # Set up the program in the image (separate file system)
# COPY SID_onefile /opt/program
# WORKDIR /opt/program

# # RUN chmod +x /opt/ml/model/serve


FROM python:3.6

# first layers should be dependency install so changes in code won't cause the build to
# start from scratch.
COPY requirements.txt /opt/program/requirements.txt

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         wget \
         nginx \
         ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir -r /opt/program/requirements.txt

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"
ENV MODEL_PATH="/opt/ml/model"
# Default timeout is 12 hours
ENV SAGEMAKER_MODEL_SERVER_TIMEOUT=43200
ENV MODEL_SERVER_TIMEOUT=43200

# Set up the program in the image
COPY model /opt/program
WORKDIR /opt/program

