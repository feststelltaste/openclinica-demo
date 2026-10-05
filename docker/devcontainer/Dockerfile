FROM mcr.microsoft.com/devcontainers/java:1-17-bookworm

# The base image currently contains a Yarn APT source whose expired/missing
# signing key prevents Dev Container features from running apt-get update.
# OpenClinica does not use Yarn, so remove that repository before features run.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# python3-ipykernel provides the kernel for Jupyter notebooks.
# The base image ships only a minimal Python without the standard library
# modules (for example json) that docker/test/generate_demo_sql.py needs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 libpython3-stdlib python3-ipykernel python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Debian bookworm has no jupyterlab package. Codespaces' "JupyterLab" option
# needs `jupyter lab` on the PATH, so install it into its own venv.
RUN python3 -m venv /opt/jupyter \
    && /opt/jupyter/bin/pip install --no-cache-dir jupyterlab ipykernel \
    && ln -s /opt/jupyter/bin/jupyter /usr/local/bin/jupyter \
    && ln -s /opt/jupyter/bin/jupyter-lab /usr/local/bin/jupyter-lab

# Node.js and the Pi coding agent. This is installed here and not with the
# Dev Container node feature because features are applied after this file.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g --ignore-scripts @earendil-works/pi-coding-agent
