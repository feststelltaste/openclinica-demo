# OpenClinica Demo – Workshop

This file contains the notes for workshop participants: Codespaces, Docker, demo data, rebuilds and the coding agent.
For the general project description see [README.md](README.md).

## Working in GitHub Codespaces

The easiest way to take part is a codespace: a ready-to-use development
environment in your browser (or in VS Code), so you do not have to install
anything.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/feststelltaste/openclinica-demo?quickstart=1)

1. Click the badge above, or use `Code` → `Codespaces` → `Create codespace on master`
   in the repository. Choose a machine with at least four CPU cores.
2. Wait a few minutes. While the codespace is created, it starts the demo
   installation from prebuilt images (OpenClinica and PostgreSQL with the demo
   data already loaded) and installs the tools: JDK, Maven, Docker, the coding
   agents and JupyterLab.
3. Open the `PORTS` tab, select port `8080` and open its forwarded address; it
   redirects to OpenClinica. Sign in with `root` / `openclinica`.

Good to know:

- Forwarded ports are private to your GitHub account by default. Do not make
  them public: the installation uses known credentials.
- Everything runs inside the codespace. Stop it when you take a break; deleting
  it also deletes its Docker volumes, the database and uploaded CRFs.
- Notebooks open in the editor once you pick the Python kernel. For the
  JupyterLab interface run `jupyter lab` in the terminal and open port `8888`
  in the `PORTS` tab; it needs no token.

## Dev Container on your own computer

If you do not want to use a codespace, you can run the same environment (JDK,
Maven, Docker, the coding agents and JupyterLab) as a Dev Container on your own
computer. You need:

- [Docker](https://docs.docker.com/get-docker/) with at least 4 CPU cores and
  8 GB RAM available
- [Git](https://git-scm.com/) and [VS Code](https://code.visualstudio.com/) with
  the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
  extension

1. Clone the repository and open it in VS Code:

   ```bash
   git clone https://github.com/feststelltaste/openclinica-demo.git
   code openclinica-demo
   ```

2. Run `Dev Containers: Reopen in Container` from the command palette (`F1`).
   The first start pulls the image and takes a few minutes.
3. When the container is up, it starts the demo installation (PostgreSQL and
   OpenClinica) automatically. The terminal prints the URL; open
   <http://127.0.0.1:8080/OpenClinica/MainMenu> and sign in with
   `root` / `openclinica`.
4. Set up the coding agent as described in
   [Coding agent with LiteLLM](#coding-agent-with-litellm). Unlike in a
   codespace, run `./setup.sh` yourself and enter the URL and key.

To build and run your own code changes inside the Dev Container, stop the demo
installation first (it uses the same port 8080) and use the rebuild script:

```bash
docker compose -f docker/docker-compose.demo.yml down
bash docker/rebuild.sh
```

### Dev Container with Bash only (no VS Code)

You can also start the Dev Container from a shell with the
[Dev Container CLI](https://github.com/devcontainers/cli). You need Docker, Git
and Node.js (for `npm`). The steps use Bash syntax. They are tested on WSL2
with Docker Engine; Linux works the same way, macOS is untested.

```bash
git clone https://github.com/feststelltaste/openclinica-demo.git
cd openclinica-demo
npm install -g @devcontainers/cli
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . /bin/bash
```

The last command opens a shell inside the container; run it again in a second
terminal whenever you need another one. Inside the shell JDK, Maven, Docker,
`pi`, `claude` and `jupyter` are available, and `./setup.sh` sets up the coding
agent.

Two differences to VS Code:

- Start the demo installation yourself if it is not running yet (the container
  start is supposed to do it, but check with
  `docker compose -f docker/docker-compose.demo.yml ps`):

  ```bash
  docker compose -f docker/docker-compose.demo.yml up -d
  ```

- The CLI does not forward ports. Inside the container `curl` reaches
  `http://localhost:8080` directly; for your browser, publish the port from a
  shell on your computer (not in the container). Pick a free host port if 8080 is
  taken, here `18080`:

  ```bash
  ip=$(docker inspect "$(docker ps -q --filter label=devcontainer.local_folder="$PWD")" \
    --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
  docker run -d --rm --name oc-forward -p 18080:8080 alpine/socat \
    tcp-listen:8080,fork,reuseaddr tcp-connect:$ip:8080
  ```

  Then open <http://127.0.0.1:18080/OpenClinica/MainMenu>. Remove the forward
  with `docker rm -f oc-forward`.

To stop and remove the container: `docker rm -f $(docker ps -aq --filter label=devcontainer.local_folder="$PWD")`.

## Demo installation on your own computer

This variant needs no Dev Container: only Docker with Docker Compose, directly
on your machine. Use the section above if you want the complete tool set.

This is the quickest way to try OpenClinica locally. It uses a prebuilt image
of a released demo version, so neither Maven nor a JDK is needed. Only Docker
with Docker Compose is required.

Start OpenClinica from the repository root:

```bash
docker compose -f docker/docker-compose.demo.yml up -d
```

The command pulls the images and starts PostgreSQL and OpenClinica. The demo
data is already part of the database image and is restored on the first start
with an empty volume. The first start can take a few minutes; follow it with
`docker compose -f docker/docker-compose.demo.yml logs -f openclinica`.
Afterwards, open <http://127.0.0.1:8080/OpenClinica/MainMenu> and sign in with
the initial test account `root` / `openclinica`. The credentials are for local
testing only.

The demo data consists of eight simple English studies with 20 synthetic
subjects each (160 in total), complete visits, forms, and everyday habit data.
No real personal data is used.

To get back to the original demo data, remove the database and start again:

```bash
docker compose -f docker/docker-compose.demo.yml down --volumes
docker compose -f docker/docker-compose.demo.yml up -d
```

Stop the containers while retaining the data:

```bash
docker compose -f docker/docker-compose.demo.yml down
```

Add `--volumes` to remove the database and uploaded files as well (this is what the reset above does).

## Local development build

To run your own code changes, build the application yourself. This requires
Maven, JDK 17 for the build, Docker, and Docker Compose.

```bash
mvn -DskipTests package
docker compose -f docker/docker-compose.test.yml up -d
```

The first start creates and migrates the database and can take a few minutes.
Follow it with `docker compose -f docker/docker-compose.test.yml logs -f openclinica`.
To reset the database and load the demo data, run
`bash docker/demo/reset-demo-data.sh --yes`. Without `COMPOSE_FILE`, the script
uses `docker/docker-compose.test.yml`.

## Rebuild the application and restart Docker

After changing the code, build the WAR and recreate the OpenClinica container
with one command from the repository root:

```bash
bash docker/rebuild.sh
```

The script runs `mvn -B -DskipTests package`, starts the
`docker/docker-compose.test.yml` stack if it is not running yet and recreates
the `openclinica` container so that it picks up the new WAR. It then waits up
to five minutes until the login page responds and prints the URL to open
(sign in with `root` / `openclinica`). In a codespace this is the forwarded
address of port `8080`.

To restart without building again, for example after a failed start:

```bash
bash docker/rebuild.sh --no-build
```

Useful commands:

```bash
docker compose -f docker/docker-compose.test.yml logs -f openclinica   # follow the log
docker compose -f docker/docker-compose.test.yml down                  # stop, keep data
bash docker/demo/reset-demo-data.sh --yes                              # reset the database and reload the demo data
```

## Coding agent with LiteLLM

The workshop uses the coding agents [Pi](https://pi.dev) (`pi`) and
[Claude Code](https://claude.com/claude-code) (`claude`). Both talk to a
LiteLLM instance, so you need its URL and an API key from the workshop team.

Run the setup once in the terminal and enter the URL, the API key and, if you
like, a different default model (press Enter for `eu.glm-53-flash`):

```bash
./setup.sh
```

The script configures Pi and Claude Code and checks that the key works; if the
check fails, it offers to ask for the values again. The first terminal of a new
codespace offers to run it for you; type `s` to skip. Afterwards start an agent
with `pi` or `claude`.

Available models: `eu.glm-53-flash` (default), `eu.deepseek-v4.1-flash` and
`eu.qwen3.8-flash-next`. In Pi switch with `/model`. In Claude Code the same
models appear in the `/model` menu as Sonnet (GLM Flash, default), Opus
(DeepSeek) and Haiku (Qwen). Claude Code asks before running commands or
editing files; press `Shift+Tab` to switch to auto mode.

The key is stored only in your codespace (`~/.pi/agent/models.json` and
`~/.claude/settings.json`). Do not commit it.
