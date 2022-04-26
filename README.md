# (PoC) 'Arkive' multi-provider archival API

A simple API to quickly and easily archive an url to multiple providers.

## Getting started

To get the dev environment going, there are two options:

### Using poetry

Make sure you have [poetry installed](https://python-poetry.org/docs/#installation)

```bash
poetry install
poetry run run
```

To access it on the internet, don't expose uvicorn but use a reverse proxy in front, e.g. with caddy:

```Caddyfile
reverse_proxy 127.0.0.1:3223
```

### With Nix

Arkive is also packaged as a Nix flake:

```bash
nix build
./results/bin/run
```

## How to deploy

- set `ARKIVE_DB_PATH` to your sqlite database's path
- change `ARKIVE_PORT` if desired


### using Nix flakes:

The nix package comes with a nixosModule which sets up a systemd service

Add arkive-api to your flake inputs:

```nix
    arkive-api = {
      url = "github:xamogast/arkive-api";
    };
```

The module is at `inputs.arkive-api.nixosModule.x86_64-linux` (replace ending wwith your system) -- import this into your desired hosts, then enable the service, and set the path to the db:

```nix
services.arkive-api.enable = true;
services.arkive-api.db_path = "/data/arkive.db";
```


## Development

Install Nix, the package manager, then simply run `nix develop` to get a full dev environment.


## 0.0.1 PoC requirements:
- DONE ~user is able to submit a website by e.g. navigating to `arkive.ml/https://www.theonion.com/the-onion-guide-to-tipping-1848821007`~
- DONE ~submitted urls are saved to an sqlite db with the original url and the archived url~
- DONE ~API returns the archived url in a json response~
- DONE ~remove any URL schemas like `http://` .. etc to avoid duplicates in DB~
- DONE ~working archive.org provider implemented~


## Planned features and additions
- DONE ~store url to db as first step, add archive urls to record later~
- TODO [#A] use [freeze-dry](https://github.com/WebMemex/freeze-dry) to save a single file copy of the page to `$freezedry_dir`
- TODO add more providers
- TODO embed annotations.js into the freeze-dried sites
    - where to store annotations? writing it to the doc changes the hash

