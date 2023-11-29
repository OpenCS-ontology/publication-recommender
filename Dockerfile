FROM python:3.10.9-slim-bullseye

COPY requirements.txt /home/requirements.txt
COPY merge_graphs.py /home/merge_graphs.py
COPY similar_papers.py /home/similar_papers.py
COPY container_test /home/container_test

RUN apt-get update
RUN apt-get install -y git
RUN pip3 install -r /home/requirements.txt

RUN mkdir /home/input_ttl_files
RUN mkdir /home/output
