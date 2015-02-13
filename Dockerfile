FROM serfnode

MAINTAINER Walter Moreira <wmoreira@tacc.utexas.edu>

RUN apt-get update -y && \
    apt-get install -y git libncurses5-dev git python3 python3-pip python3-dev

COPY requirements.txt /requirements.txt
WORKDIR /
RUN pip3 install -r requirements.txt

COPY stubs/ /stubs
ENV MYPYPATH /stubs
COPY adama/ /adama
COPY handler /handler

WORKDIR /adama
