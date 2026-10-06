# Welcome!

OpenClinica is an open source software for Electronic Data Capture (EDC) and Clinical Data Management (CDM) used to optimize clinical trial workflow in a smart and secure fashion. Use OpenClinica to:

- Build studies
- Create eCRFs
- Design rules/edit checks
- Schedule patient visits 
- Capture eCRF data from study sites via the web
- Monitor and manage clinical data
- Audit trails and electronic signatures
- Role-based access controls
- Import/Export Data
- Extract data for analysis and reporting
- and much more!

## Getting Started

- [System requirements](https://docs.openclinica.com/installation/system-requirements)
- [Report an issue](https://jira.openclinica.com/)
- [Release notes](https://docs.openclinica.com/release-notes)
- [Extensions/Contributions](https://community.openclinica.com/extensions)
- [Installation](https://github.com/OpenClinica/OpenClinica/wiki)

## Demo installation on your own computer

This is the quickest way to try OpenClinica locally. It uses a prebuilt image
of a released demo version, so neither Maven nor a JDK is needed. Only Docker
with Docker Compose is required.

Start OpenClinica and load the synthetic demo data from the repository root:

```bash
COMPOSE_FILE=docker/docker-compose.demo.yml bash docker/test/reset-demo-data.sh --yes
```

The command pulls the image, starts PostgreSQL and OpenClinica, waits until the
database schema exists and then loads the demo data. The first start can take a
few minutes. Afterwards, open <http://127.0.0.1:8080/OpenClinica/MainMenu> and
sign in with the initial test account `root` / `openclinica`. The credentials are
for local testing only.

The demo data consists of eight simple English studies with 20 synthetic
subjects each (160 in total), complete visits, forms, and everyday habit data.
No real personal data is used. Running the command again deletes the database
and recreates the data.

Stop the containers while retaining the data:

```bash
docker compose -f docker/docker-compose.demo.yml down
```

Add `--volumes` to remove the database and uploaded files as well.

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
`bash docker/test/reset-demo-data.sh --yes`. Without `COMPOSE_FILE`, the script
uses `docker/docker-compose.test.yml`.

## GitHub Codespaces

The repository includes a development-container configuration. Create a
codespace with at least four CPU cores. On creation, it starts the demo
installation from the prebuilt images; the demo data is already part of the
database image. Open the `PORTS`
tab, select port `8080` and open its forwarded address; it redirects to
OpenClinica. Sign in with `root` / `openclinica`. Forwarded ports are private by
default; do not make this installation public because it uses known credentials.

### Coding agent and notebooks

The container includes the [Pi](https://pi.dev) coding agent with the
`pi-subagents` extension, [Claude Code](https://claude.com/claude-code), and
JupyterLab with a Python kernel for notebooks.

Pi talks to a LiteLLM instance. Run this once in the terminal and enter the URL
and API key you were given:

```bash
./setup.sh
```

The first terminal in a new codespace offers to do this for you; type `s` to
skip it. Then start the agent with `pi` or `claude`.

The default model is `eu.deepseek-v4.1-flash`; `eu.glm-53-flash` and
`eu.qwen3.8-flash-next` are available through `/model` in Pi. Claude Code uses
the same LiteLLM connection through its Anthropic-compatible API: DeepSeek is
Sonnet (the default), GLM is Opus and Qwen is Haiku in its `/model` menu. The
key is stored only in the home directory of the codespace
(`~/.pi/agent/models.json`, `~/.claude/settings.json`).
Maintainers can instead set the Codespaces secrets `LITELLM_URL` and
`LITELLM_API_KEY` (optionally the environment variable `LITELLM_MODEL` for a
different default model); they are picked up when the codespace is created.

The development container itself is a prebuilt image
(`ghcr.io/feststelltaste/openclinica-demo-devcontainer:latest`, built from
`docker/devcontainer/`). The workflow `Devcontainer-Image` rebuilds it whenever
something in that folder changes on `master`; it can also be started manually.
The package must be public. Settings, extensions and the start commands stay in
`.devcontainer/devcontainer.json` and need no image rebuild.

Deleting a codespace also deletes its Docker volumes and uploaded CRFs.

### Notes for maintainers

The demo image is not built on every push, but only for a deliberately released
state:

1. Develop and test the changes.
2. Tag the state, for example `git tag demo-v4 && git push origin demo-v4`.
3. The GitHub Actions workflow `Demo-Image` builds the WAR and publishes
   `ghcr.io/feststelltaste/openclinica-demo:demo-v4` and
   `ghcr.io/feststelltaste/openclinica-demo-db:demo-v4`. Wait until it is green.
4. Set the image tags in `docker/docker-compose.demo.yml` to the new version and commit.

The workflow publishes two images for the tag: `openclinica-demo` contains the
application, `openclinica-demo-db` is PostgreSQL with the migrated database and
the demo data. The data is generated reproducibly by
`docker/test/reset-demo-data.sh` and dumped by `docker/test/dump-demo-data.sh`;
the database image restores it on the first start with an empty volume. Both
packages must be public so that codespaces and other computers can pull them
without logging in. Set the tag in `docker/docker-compose.demo.yml` for both images.

## Request a feature

To request a feature please submit a ticket on [Jira](https://jira.openclinica.com/) or start a discussion on the [OpenClinica Forum](http://forums.openclinica.com).

## Screenshots
![Imgur](http://i.imgur.com/ACXj3L7.jpg "Home screen") 
![Imgur](http://i.imgur.com/DqHQ05Z.jpg "Subject Matrix")



## License

[GNU LGPL license](https://www.openclinica.com/gnu-lgpl-open-source-license)
