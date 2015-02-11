FROM serfnode

MAINTAINER Walter Moreira <wmoreira@tacc.utexas.edu>

RUN apt-get update -y && \
    apt-get install -y git libncurses5-dev git python3 python3-pip python3-dev

COPY adama-package/requirements.txt /adama-package/requirements.txt
WORKDIR adama-package/
RUN pip3 install -r requirements.txt

ENV MYPYPATH /adama-package/stubs
COPY adama-package/ /adama-package

COPY handler /handler
COPY serfnode.yml /serfnode.yml
COPY deploy.yml /deploy/
