FROM python:3.12-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install --no-cache-dir build && python -m build --wheel

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    zsh \
    fish \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

RUN mkdir -p /root/.shellsense && chmod 0700 /root/.shellsense

ENV SHELL=/bin/bash
ENV TERM=xterm-256color

ENTRYPOINT ["ss"]
CMD ["--help"]
