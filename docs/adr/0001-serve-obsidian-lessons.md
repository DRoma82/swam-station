# Serve Obsidian lessons through NPM

Status: Accepted

Use an internal-only `lessons` Nginx service. It mounts the Obsidian lessons directory read-only, so only Nginx Proxy Manager can reach it and the site cannot change lesson content.

Nginx exposes its built-in JSON autoindex under `/api/`; a small Vue page renders that data as a directory browser. This keeps new folders and HTML pages visible without a site build. NPM provides the existing Secure Homelab access list and wildcard certificate 40 for `learn.dannyroma.ca`.

To roll back, remove the `lessons` service and its NPM proxy host, then recreate the retired `tinfoil` service only if needed. The former `/mnt/seagate/tinfoil` content is not part of this change.
