FROM mcr.microsoft.com/devcontainers/java:1-17-bookworm

# The base image currently contains a Yarn APT source whose expired/missing
# signing key prevents Dev Container features from running apt-get update.
# OpenClinica does not use Yarn, so remove that repository before features run.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# python3-ipykernel provides the kernel for Jupyter notebooks.
# The base image ships only a minimal Python without the standard library
# modules (for example json) that docker/test/generate_demo_sql.py needs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 libpython3-stdlib python3-ipykernel \
    && rm -rf /var/lib/apt/lists/*
