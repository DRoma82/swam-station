# AGENTS.md

Instructions and current-state reference for agents working on this home-lab Docker repository.

## Repository purpose

This repository manages the Swam Station home-lab Docker Compose stack.

Primary file:

```text
docker-compose.yaml
```

The working tree is live production configuration on the host. Treat changes as production changes.

## Git and ignored state

Git tracks the Compose/config source. Runtime state and secrets are intentionally ignored.

Important ignored/private paths:

```text
.env
.secrets.env
.duck_token
apps/
letsencrypt/
```

Do not commit secrets or live app state. If examples are needed, create `*.example` files with fake values only.

## Secret handling

- Never expose real secrets, tokens, API keys, passwords, cert private keys, or session tokens in final responses.
- Redact sensitive shell output before sharing.
- Keep `.env`, `.secrets.env`, `.duck_token`, `apps/`, and `letsencrypt/` untracked.
- Prefer least-privilege secret exposure. Do not pass broad secret files to more containers than necessary without a reason.

## Standard workflow

Before changing files or service state:

1. Inspect the relevant config and current runtime state.
2. Make the smallest targeted change.
3. Validate Compose:

   ```bash
   docker compose -f docker-compose.yaml config --quiet
   ```

4. Restart/recreate only affected services.
5. Verify with `docker compose ps`, logs, and targeted checks.

When editing Nginx Proxy Manager state directly, back up its DB first:

```bash
cp -a apps/nginx-proxy-manager/database.sqlite \
  apps/nginx-proxy-manager/database.sqlite.bak-before-<change>-$(date +%Y%m%d%H%M%S)
```

## Network and exposure model

- Router forwards external traffic only to ports `80` and `443`.
- Many app UI ports are intentionally published for LAN-only fallback access if NPM fails.
- Do not remove LAN UI port mappings just because they are published.
- Avoid broad Docker network segmentation unless it creates a real boundary. A proxy network containing nearly every container is not useful.
- Useful targeted segmentation candidate: isolate `homepage` and `docker-socket-proxy` on a small internal-only network.

## Current service state and expectations

### Nginx Proxy Manager

Service: `npm`

Persistent mounts:

```yaml
./apps/nginx-proxy-manager:/data
./letsencrypt:/etc/letsencrypt
```

Current certificate model:

```text
Wildcard certificate: dannyroma.ca, *.dannyroma.ca
NPM cert id: 40
Live path: /etc/letsencrypt/live/npm-40/
```

All active NPM proxy hosts should use certificate id `40`.

Only the wildcard certificate should remain active. Individual per-subdomain certs are not expected.

When changing NPM configs:

```bash
docker compose exec -T npm nginx -t
docker compose exec -T npm nginx -s reload
```

NPM generated configs live under:

```text
apps/nginx-proxy-manager/nginx/proxy_host/
apps/nginx-proxy-manager/nginx/redirection_host/
```

### Cloudflare/DDNS

Service: `ddclient`

Cloudflare DDNS should update only:

```text
dannyroma.ca
*.dannyroma.ca
```

Do not re-add individual subdomain updates such as `home.dannyroma.ca`, `sonarr.dannyroma.ca`, etc. The wildcard A record handles one-label subdomains.

DuckDNS update for `droma82` is currently present and may remain unless requested otherwise.

Useful check:

```bash
docker compose logs --tail=100 ddclient
for d in dannyroma.ca '*.dannyroma.ca' home.dannyroma.ca ha.dannyroma.ca; do
  dig +short @1.1.1.1 A "$d"
done
```

### Homepage

Service: `homepage`

Homepage uses Docker status through `docker-socket-proxy`, not through a raw Docker socket mount.

`homepage/docker.yaml` should point to:

```yaml
swam-station-docker:
  host: docker-socket-proxy
  port: 2375
```

Homepage background image is local:

```text
homepage/images/inside-the-hatch.webp
```

Compose should mount it to:

```yaml
./homepage/images:/app/public/images:ro
```

Homepage settings should reference:

```yaml
background:
  image: /images/inside-the-hatch.webp
```

The NPM host for `home.dannyroma.ca` intentionally disables caching to avoid stale Next.js asset/HTML mismatches. Preserve no-cache behaviour unless intentionally redesigning caching.

Home Assistant widget/checks use:

```text
http://host.docker.internal:8123
```

Homepage requires an `extra_hosts` entry for:

```yaml
host.docker.internal:host-gateway
```

### Docker socket proxy

Service: `docker-socket-proxy`

This service is the only container that should mount `/var/run/docker.sock` for Homepage status access.

Expected posture:

```yaml
POST=0
```

Do not give Homepage direct raw Docker socket access unless explicitly requested.

### Home Assistant

Service: `homeassistant`

Home Assistant uses host networking:

```yaml
network_mode: host
```

This is required for reliable HomeKit/mDNS/Bonjour behaviour in the current setup. Do not revert to bridge mode without considering HomeKit discovery.

Because HA is host-networked:

- NPM should not proxy to `homeassistant:8123`.
- Homepage should not use `homeassistant:8123`.
- NPM HA proxy hosts currently forward to the host from Docker bridge side, e.g. `172.17.0.1:8123`.
- Homepage uses `host.docker.internal:8123`.

Home Assistant reverse proxy config should trust the Docker proxy network. Current config includes:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.18.0.0/16
```

If Docker subnets change, update `trusted_proxies`.

Entity modelling expectations:

- Person presence requires a `device_tracker` assigned to the person.
- Physical lights exposed as `switch.*` should ideally be converted to `light.*` via helpers/Switch-as-X.
- Diagnostic/control switches such as Kasa LED or auto-update toggles should be disabled if they pollute Homepage/HomeKit counts.
- Media play/pause/stop actions should be `script.*` or `button.*`, not `switch.*`.

### Jellyfin

Service: `jellyfin`

Current expectations:

- TLS is handled by NPM.
- Jellyfin should not mount `./letsencrypt`.
- DLNA/SSDP is disabled.
- `1900/udp` should remain absent unless DLNA is intentionally restored.
- `7359/udp` may remain for Jellyfin discovery.
- Host networking is not needed for Jellyfin in the current state.

### qBittorrent

Service: `qbittorrent`

Current expectations:

- No `/watch` mount.
- `watched_folders.json` should be empty or not configured for `/watch`.
- Homepage qBittorrent widget username is `dani`.

### Watchtower

Service: `watchtower`

Expected settings:

```yaml
WATCHTOWER_SCHEDULE=0 0 4 * * *
DOCKER_API_VERSION=1.40
```

Watchtower intentionally mounts the Docker socket and should be treated as privileged.

## Useful checks

```bash
# Compose validation
docker compose -f docker-compose.yaml config --quiet

# Service status
docker compose ps

# NPM config validation
docker compose exec -T npm nginx -t

# Wildcard cert SNI check
for h in home.dannyroma.ca ha.dannyroma.ca jellyfin.dannyroma.ca sonarr.dannyroma.ca; do
  echo | openssl s_client -connect 127.0.0.1:443 -servername "$h" 2>/dev/null \
    | openssl x509 -noout -subject -dates
done

# Homepage checks
curl -k -I https://home.dannyroma.ca/
curl -k -I https://home.dannyroma.ca/images/inside-the-hatch.webp

# Home Assistant checks
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8123
curl -k -sS -o /dev/null -w '%{http_code}\n' https://ha.dannyroma.ca

# DNS/DDNS checks
docker compose logs --tail=100 ddclient
for d in dannyroma.ca '*.dannyroma.ca' home.dannyroma.ca ha.dannyroma.ca; do
  dig +short @1.1.1.1 A "$d"
done
```

## Do not do without explicit approval

- Do not commit secrets or live app state.
- Do not delete `apps/` or `letsencrypt/` wholesale.
- Do not change Home Assistant away from host networking.
- Do not remove LAN fallback UI ports solely because they are published.
- Do not re-add individual Cloudflare A-record updates to ddclient.
- Do not reintroduce removed stats services.
- Do not enable broad HSTS without confirming every relevant subdomain works over HTTPS.
- Do not give Homepage direct raw Docker socket access.
