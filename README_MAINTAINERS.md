# OpenClinica Demo – Maintainers

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/feststelltaste/openclinica-demo?quickstart=1)

This file is for maintainers of the workshop setup: releases, tags and image publishing.
Participants only need [README_WORKSHOP.md](README_WORKSHOP.md).

## Releasing the demo images

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
`docker/demo/reset-demo-data.sh` and dumped by `docker/demo/dump-demo-data.sh`;
the database image restores it on the first start with an empty volume. Both
packages must be public so that other computers can pull them
without logging in. Set the tag in `docker/docker-compose.demo.yml` for both images.

## Development container image

The development container is a prebuilt image
(`ghcr.io/feststelltaste/openclinica-demo-devcontainer:latest`, built from
`docker/devcontainer/`). It already contains the Maven dependencies of the
project, so the first `mvn package` needs no downloads. The workflow
`Devcontainer-Image` rebuilds it whenever something in that folder or one of the
`pom.xml` files changes on `master`; it can also be started manually.
The package must be public. Settings, extensions and the start commands stay in
`.devcontainer/devcontainer.json` and need no image rebuild.

## LiteLLM defaults for codespaces

Instead of each participant running `./setup.sh`, maintainers can set the
Codespaces secrets `LITELLM_URL` and `LITELLM_API_KEY` (optionally the environment
variable `LITELLM_MODEL` for a different default model); they are picked up when
the codespace is created.