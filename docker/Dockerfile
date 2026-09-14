FROM rust:bookworm

# Install build essentials and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ca-certificates \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

ENV CARGO_HOME=/root/.cargo
ENV CARGO_TARGET_DIR=/root/target
ENV PATH="/root/.cargo/bin:/usr/local/bin:${PATH}"

CMD ["bash", "/workspace/docker/run-tests.sh"]
