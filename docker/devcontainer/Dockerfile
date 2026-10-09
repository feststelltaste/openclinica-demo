# Stage 1: build the project once so that all Maven dependencies and plugins
# are downloaded. Only the resulting repository is kept in the final image.
FROM mcr.microsoft.com/devcontainers/java:1-17-bookworm AS maven-repository
ENV JAVA_HOME=/usr/lib/jvm/msopenjdk-current
# Same Maven version as the Dev Container java feature installs (mavenVersion in
# devcontainer.json), so that the cached plugin versions match.
RUN curl -fsSL https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz \
    | tar -xz -C /opt \
    && ln -s /opt/apache-maven-3.9.9/bin/mvn /usr/local/bin/mvn
COPY . /src
RUN cd /src && mvn -B -q -DskipTests -Dmaven.repo.local=/m2repo package

FROM mcr.microsoft.com/devcontainers/java:1-17-bookworm

# The base image currently contains a Yarn APT source whose expired/missing
# signing key prevents Dev Container features from running apt-get update.
# OpenClinica does not use Yarn, so remove that repository before features run.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# python3-ipykernel provides the kernel for Jupyter notebooks. ripgrep and
# fd-find are used by the Pi coding agent (Debian names the binary fdfind).
# The base image ships only a minimal Python without the standard library
# modules (for example json) that docker/demo/generate_demo_sql.py needs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 libpython3-stdlib python3-ipykernel python3-venv \
        ripgrep fd-find \
    && ln -s "$(command -v fdfind)" /usr/local/bin/fd \
    && rm -rf /var/lib/apt/lists/*

# Debian bookworm has no jupyterlab package. Codespaces' "JupyterLab" option
# needs `jupyter lab` on the PATH, so install it into its own venv.
RUN python3 -m venv /opt/jupyter \
    && /opt/jupyter/bin/pip install --no-cache-dir jupyterlab ipykernel \
    && ln -s /opt/jupyter/bin/jupyter /usr/local/bin/jupyter \
    && ln -s /opt/jupyter/bin/jupyter-lab /usr/local/bin/jupyter-lab

# Node.js, the Pi coding agent and Claude Code. This is installed here and not with the
# Dev Container node feature because features are applied after this file.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g --ignore-scripts @earendil-works/pi-coding-agent \
    && npm install -g @anthropic-ai/claude-code

# CodeCharta analysis tools (ccsh) for the code maps. They need a JDK, which
# the image already has (see JAVA_HOME in devcontainer.json).
ARG CODECHARTA_ANALYSIS_VERSION=2.1.0
RUN curl -fsSL "https://github.com/MaibornWolff/codecharta/releases/download/ana-${CODECHARTA_ANALYSIS_VERSION}/codecharta-analysis-${CODECHARTA_ANALYSIS_VERSION}.tar" \
    | tar -x -C /opt --one-top-level=codecharta-analysis --strip-components=1 \
    && ln -s /opt/codecharta-analysis/bin/ccsh /usr/local/bin/ccsh

# Maven repository with all dependencies, so the first build works offline-fast.
RUN mkdir -p /home/vscode/.m2 && chown vscode:vscode /home/vscode/.m2
COPY --from=maven-repository --chown=vscode:vscode /m2repo /home/vscode/.m2/repository
