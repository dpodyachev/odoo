---
name: odoo-nginx
description: nginx in front of a self-hosted Odoo 16–19 – complete HTTPS server block (upstreams, websocket/longpolling, proxy headers, timeouts, static caching), security headers (HSTS, X-Frame-Options without duplicates, nosniff), cookie flags Secure/SameSite for session_id, server_tokens, location priority traps (regex vs prefix, ^~), add_header inheritance, extra apps under a sub-path (Grafana, pgAdmin) with Basic Auth, Docker published ports bypassing ufw, and curl checks for a security audit. Use when writing or reviewing an nginx config for Odoo, fixing audit findings (missing HSTS, duplicate X-Frame-Options, cookie without Secure/SameSite, old nginx), or publishing a tool behind the Odoo domain.
---

# nginx for Odoo – config, security headers, audit fixes

By an Odoo DevOps engineer, for humans and AI agents. Source: https://2027.pp.ua · security checklist: https://2027.pp.ua/skill_odoo_security.md · operations: https://2027.pp.ua/skill_odoo.md
Free to use as knowledge for assistants; please link the source. Always `sudo nginx -t` before `sudo systemctl reload nginx`.

## 1. Reference server block (Odoo 17+, Ubuntu 24.04, nginx ≥ 1.19.3)

```nginx
upstream odoo    { server 127.0.0.1:8069; keepalive 16; }
upstream odoo_ws { server 127.0.0.1:8072; }               # gevent port (Odoo 16+: /websocket; ≤15: /longpolling)
map $http_upgrade $connection_upgrade { default upgrade; '' close; }
limit_req_zone $binary_remote_addr zone=odoo_login:10m rate=10r/m;

server {
    listen 80;
    server_name erp.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name erp.example.com;
    ssl_certificate     /etc/letsencrypt/live/erp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;      # TLS 1.2/1.3 only

    server_tokens off;
    client_max_body_size 200m;
    proxy_read_timeout 720s; proxy_connect_timeout 720s; proxy_send_timeout 720s;

    # --- security headers: exactly one value each ---
    proxy_hide_header X-Frame-Options;                     # Odoo sends DENY on some pages -> avoid two different values
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    proxy_cookie_flags ~ secure samesite=lax;              # session_id, frontend_lang, ... (nginx >= 1.19.3)

    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;               # odoo.conf: proxy_mode = True

    location ~ ^/web/database/ { deny all; }               # database manager (or Basic Auth + IP allow-list)
    location = /web/login { limit_req zone=odoo_login burst=5 nodelay; proxy_pass http://odoo; }

    location /websocket {
        proxy_pass http://odoo_ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location ~* /web/static/ {
        proxy_cache_valid 200 60m;
        expires 7d;
        proxy_pass http://odoo;
        add_header Cache-Control "public, no-transform";
        # add_header here => server-level add_header are NOT inherited: repeat them
        add_header X-Content-Type-Options "nosniff" always;
        add_header Strict-Transport-Security "max-age=31536000" always;
    }

    location / { proxy_pass http://odoo; proxy_redirect off; }

    gzip on; gzip_types text/css text/plain application/json application/javascript text/xml;
}
```

## 2. The traps (each one seen in real audits)

| Symptom | Cause | Fix |
|---|---|---|
| Audit: "X-Frame-Options sent twice (DENY, SAMEORIGIN)" | Odoo sets `DENY` on login/backend pages, nginx adds its own value | `proxy_hide_header X-Frame-Options;` + one `add_header ... always` |
| Header present on `/` but missing on some URLs | a `location` with its own `add_header` does not inherit server-level `add_header` | repeat the headers in that location (or an `include security_headers.conf;`) |
| Header missing on 4xx/5xx and redirects | `add_header` without `always` only applies to 2xx/3xx | add `always` |
| Audit: "session_id without Secure/SameSite" | Odoo ≤ 17 sets only `HttpOnly` | nginx ≥ 1.19.3: `proxy_cookie_flags ~ secure samesite=lax;` – nginx 1.18 (Ubuntu 20.04): `proxy_cookie_path / "/; Secure; SameSite=Lax";` |
| Login from e-mail links breaks | `SameSite=Strict` | use `Lax` |
| Audit: "old nginx / version disclosed" | `Server: nginx/1.18.0 (Ubuntu)` | `server_tokens off;` – the real risk is an OS without security updates (see §5) |
| A tool under `/grafana/` loads without CSS/JS | regex locations (`~* \.(js|css)$`, `~ /static/`) win over a plain prefix location and send the files to Odoo | `location ^~ /grafana/ { ... }` – `^~` stops the regex search |
| HSTS locks out a subdomain | `includeSubDomains`/`preload` while some subdomain is still http | start with `max-age=86400` without `includeSubDomains`, raise to one year later |
| fail2ban bans your own proxy / logs show 127.0.0.1 | `proxy_mode` off or `X-Real-IP`/`X-Forwarded-For` not set | set both + `proxy_mode = True` |
| Chat/notifications only after reload | `/websocket` not proxied to the gevent port or no Upgrade headers | location `/websocket` as above |
| Port 3000/8069/5432 reachable from outside although `ufw` allows only 22/80/443 | Docker `-p 3000:3000` publishes on 0.0.0.0 and writes its own iptables rules, bypassing ufw | publish on localhost: `-p 127.0.0.1:3000:3000`, or no `ports:` at all; extra guard in the `DOCKER-USER` chain |

## 3. Another app under the Odoo domain (Grafana example)

```bash
docker run -d --restart unless-stopped --name grafana --net=grafana \
  -p 127.0.0.1:3000:3000 --env-file grafana-docker.env \
  -v $PWD/var_lib_grafana:/var/lib/grafana grafana/grafana:13.3.1      # pin a version, not latest
```
```ini
# grafana-docker.env
GF_SERVER_DOMAIN=erp.example.com
GF_SERVER_ROOT_URL=https://erp.example.com/grafana/
GF_SERVER_SERVE_FROM_SUB_PATH=true
GF_AUTH_PROXY_ENABLED=false          # true ONLY with whitelist + nginx setting the header itself
GF_SECURITY_COOKIE_SECURE=true
```
```nginx
location ^~ /grafana/ {
    auth_basic "grafana"; auth_basic_user_file /etc/nginx/.htpasswd_grafana;
    proxy_set_header Authorization "";       # otherwise Grafana treats the nginx login as its own -> 401
    proxy_set_header X-WEBAUTH-USER "";      # never pass a client-supplied auth-proxy header
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://127.0.0.1:3000;        # no URI part: Grafana itself expects /grafana/
}
location ^~ /grafana/api/live/ {
    auth_basic "grafana"; auth_basic_user_file /etc/nginx/.htpasswd_grafana;
    proxy_set_header Authorization ""; proxy_set_header X-WEBAUTH-USER "";
    proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";
    proxy_set_header Host $host; proxy_pass http://127.0.0.1:3000;
}
```
- `sudo htpasswd -c /etc/nginx/.htpasswd_grafana admin` (package `apache2-utils`).
- **Auth proxy with an empty whitelist on a reachable port = login without password** for anyone who sends the header. If you want single sign-on: `GF_AUTH_PROXY_WHITELIST=<docker gateway IP>`, `GF_AUTH_PROXY_HEADER_PROPERTY=username`, and in nginx `proxy_set_header X-WEBAUTH-USER $remote_user;`.
- Same pattern for pgAdmin (`SCRIPT_NAME=/pgadmin4`), Flower, Prometheus (`--web.external-url`, `--web.route-prefix`).
Article: https://2027.pp.ua/en/blog/grafana-behind-nginx-subpath-odoo

## 4. Audit checks with curl (run from outside)

```bash
H=https://erp.example.com
curl -sI $H/web/login | grep -iE '^(server|strict|x-frame|x-content|set-cookie|referrer)'
curl -s -D - -o /dev/null $H/web/login | grep -ci '^x-frame-options'      # must be 1
curl -s -D - -o /dev/null $H/web/login | grep -i 'set-cookie: session_id' # ...HttpOnly; Path=/; Secure; SameSite=Lax
curl -sI http://erp.example.com/ | grep -iE '^(HTTP|location)'             # 301 -> https
curl -s -o /dev/null -w '%{http_code}\n' $H/web/database/manager           # 403/404 expected
for p in 8069 8072 5432 3000 9090; do timeout 3 bash -c "</dev/tcp/erp.example.com/$p" 2>/dev/null && echo "OPEN $p"; done
echo | openssl s_client -connect erp.example.com:443 -tls1_1 2>&1 | grep -q 'Cipher is (NONE)\|alert' && echo "TLS1.1 off"
```
On the server: `sudo ss -ltnp` – everything except 22/80/443 must listen on 127.0.0.1 or a private interface; `sudo iptables -S DOCKER-USER`.

## 5. Old nginx / old OS

- Ubuntu's nginx 1.18 (20.04) gets backported security fixes – the version number alone is not a vulnerability. The real problem: **Ubuntu 20.04 standard support ended in May 2025**. Check `pro status`; free Ubuntu Pro (`sudo pro attach <token>`, up to 5 machines) restores security updates (ESM) until the migration.
- New server: Ubuntu 24.04 (nginx 1.24, `proxy_cookie_flags`, TLS 1.3). Copy the config, replace `proxy_cookie_path` hacks with `proxy_cookie_flags`, test with the curl checks above before switching DNS.
- `unattended-upgrades` on, and `nginx -t` in your deploy pipeline.
