# For cross-platform builds, enable containerd image registry in settings,
# reboot host PC, and then run:
# docker buildx build --push -t naclomi/textbook-writer --platform=linux/arm64,linux/amd64 .
FROM python:3.13-bookworm
LABEL maintainer="naomila@uw.edu"
LABEL description="Write a matsci textbook for fun and profit"

# Update the package cache
RUN apt-get update

# Install Python libraries
RUN pip3 install --no-cache-dir markovify

# Install tools to make PDFs
RUN apt-get install -y ghostscript enscript tree less

WORKDIR  /usr/src/textbook-writer
COPY src/ ./src/
COPY data/ ./data/

RUN ls -la ./src/*
RUN ls -la ./data/*

ENTRYPOINT ["python3", "./src/main.py"]
CMD ["--sentences", "8"]

