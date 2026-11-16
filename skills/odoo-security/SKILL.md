---
name: odoo-security
description: Hardening and protecting a self-hosted Odoo 17 instance – network exposure, nginx/TLS, database manager, admin password, users and 2FA, login brute-force protection (login cooldown, fail2ban), API keys, access rights and record rules, secure custom code (SQL injection, XSS, sudo), secrets, backups, updates, monitoring and incident response. Use when securing, auditing or reviewing an Odoo server or custom module, after a suspected compromise, or when exposing Odoo to the internet.
---

# Odoo security (Odoo 17) – hardening checklist

By an Odoo DevOps engineer, for humans and AI agents. Source: https://2027.pp.ua · operations guide: https://2027.pp.ua/skill_odoo.md
Free to use as knowledge for assistants; please link the source. Test every change on stage first.

## 0. Threat model in one minute

Most real incidents on self-hosted Odoo are not exotic: an open **database manager** (anyone can drop/backup/restore the database), **weak or reused passwords** (credential stuffing against `/web/login` and XML-RPC), **exposed ports** (8069 / PostgreSQL 5432 on the internet), **forgotten test copies** with production data, and **unpatched** Odoo or custom modules with `sudo()`/SQL mistakes.

## 1. Network: only nginx is public

- Odoo listens on localhost or a Docker network only: `http_interface = 127.0.0.1` (bare metal) or no `ports:` for the odoo container – nginx/Traefik/Cloudflare Tunnel in front.
- PostgreSQL never public: `listen_addresses = 'localhost'` (or Docker-internal), `pg_hba.conf` only for the Odoo host; Odoo's DB user **is not a superuser** (`createdb` only if you really need the database manager).
- Firewall: allow 80/443 (and SSH, ideally IP-restricted or via VPN); deny everything else. With Docker, remember published ports bypass `ufw` – do not publish what must stay internal.
- Stage/test/dev copies: never openly reachable – Basic Auth, IP allow-list, or Cloudflare Access/VPN in front (https://2027.pp.ua/en/blog/cloudflare-access-zero-trust-step-by-step).
- SSH: keys only (`PasswordAuthentication no`), no root login, fail2ban for sshd.

## 2. nginx and TLS

```nginx
server {
    listen 443 ssl http2;
    server_name erp.example.com;
    # certificates via certbot; HTTP -> HTTPS redirect in the port-80 server block
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    client_max_body_size 100m;

    # database manager / selector: not public
    location ~ ^/web/database/ { deny all; }          # or Basic Auth + IP allow-list for admins
    location = /website/info  { deny all; }           # version/modules disclosure (website module)

    # slow down password guessing
    location = /web/login { limit_req zone=odoo_login burst=5 nodelay; proxy_pass http://odoo; include odoo_proxy.conf; }

    location /websocket { proxy_pass http://odoo_ws; proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; include odoo_proxy.conf; }
    location / { proxy_pass http://odoo; include odoo_proxy.conf; }
}
# http {} level: limit_req_zone $binary_remote_addr zone=odoo_login:10m rate=10r/m;
# odoo_proxy.conf: X-Forwarded-Host/-For/-Proto, X-Real-IP;  odoo.conf: proxy_mode = True
```
- `proxy_mode = True` only behind a proxy that **overwrites** `X-Forwarded-*` – otherwise clients can spoof their IP in logs and fail2ban.
- Certificate renewal monitored (https://2027.pp.ua/en/blog/certbot-nginx-auto-renewal).
Details: https://2027.pp.ua/en/blog/nginx-apache-password-protect-odoo-database-manager

## 3. odoo.conf essentials

```ini
[options]
list_db = False                 ; hides database list and disables the manager UI
dbfilter = ^mydb$               ; one instance = one database (or ^%d$ per subdomain)
admin_passwd = <long random>    ; master password; Odoo stores it hashed (pbkdf2) when changed via the UI
proxy_mode = True
http_interface = 127.0.0.1      ; bare metal; in Docker: no published port
without_demo = all
; never on production: dev_mode / --dev, test_enable
```
- File permissions: `chmod 640 odoo.conf`, owner root, group odoo – it contains `db_password` and `admin_passwd`. Never commit it to git.
- `admin_passwd` must not be `admin` or empty; with `list_db = False` and nginx deny it is a second line, not the only one.

## 4. Users, passwords, 2FA

- **2FA** (TOTP, module `auth_totp`, in Community and Enterprise): mandatory for all internal users with admin or accounting rights. Odoo 17 can enforce it (module `auth_totp_mail_enforce` – 2FA by e-mail code for users without an app).
- Password length: Settings → General → Minimum Password Length (`auth_password_policy`, parameter `auth_password_policy.minlength`) – 12+.
- **Login brake** (built in): system parameters `base.login_cooldown_after` (failed attempts, default 5) and `base.login_cooldown_duration` (seconds, default 60) – per IP and login.
- No shared accounts; the `admin` user (id 2) gets a unique login, strong password and 2FA; daily work with personal users.
- Leavers: archive the user immediately (sessions end), rotate their API keys and any shared credentials.
- Portal/signup: `auth_signup` – "B2B (invitation only)" unless free signup is intended (Settings → Customer Account).
- Check leaked credentials of staff e-mails (Have I Been Pwned; never type the password into random sites): https://2027.pp.ua/en/blog/password-leaks-brute-force-2fa-odoo

## 5. Brute force: fail2ban on the Odoo log

Odoo logs every failed login (logger `odoo.addons.base.models.res_users`): `Login failed for db:mydb login:someone from 203.0.113.5`.
```ini
# /etc/fail2ban/filter.d/odoo-login.conf
[Definition]
failregex = ^.* Login failed for db:\S+ login:.* from <HOST>
ignoreregex =

# /etc/fail2ban/jail.d/odoo.conf
[odoo-login]
enabled  = true
port     = http,https
filter   = odoo-login
logpath  = /var/log/odoo/odoo.log
maxretry = 5
findtime = 600
bantime  = 3600
```
- Needs `proxy_mode = True` and a proxy that sets the real client IP, otherwise you ban your own nginx/Docker gateway.
- XML-RPC/JSON-RPC (`/xmlrpc/2/common`, `/jsonrpc`) logins produce the same log line – also covered.
- Behind Cloudflare: ban via Cloudflare API/WAF instead of iptables (the TCP peer is Cloudflare).

## 6. API access and integrations

- Integrations use **API keys** (Preferences → Account Security → New API Key), never the user's password; one technical user per integration with only the rights it needs.
- API keys bypass 2FA by design – treat them like passwords: store in a secret manager, rotate, delete when unused (`res_users_apikeys`).
- If no external API is needed, block `/xmlrpc/`, `/jsonrpc` at nginx (or allow only integration IPs).
- Webhooks/controllers in custom modules: `auth='user'` or a verified token – `auth='public'` + `sudo()` is a frequent hole.

## 7. Access rights and record rules

- Least privilege: users get the narrowest groups; "Settings"/"Administration" only for admins; review `res_groups` membership quarterly.
```sql
-- who has admin rights (base.group_system)
SELECT u.login, u.active FROM res_users u
  JOIN res_groups_users_rel r ON r.uid = u.id
  JOIN ir_model_data d ON d.res_id = r.gid AND d.model='res.groups' AND d.module='base' AND d.name='group_system'
 ORDER BY u.login;
-- internal users without 2FA (auth_totp installed)
SELECT login FROM res_users WHERE active AND share = false AND totp_secret IS NULL;
```
- Multi-company: check record rules (`company_ids`) – users must not see other companies' data.
- Every custom model needs `ir.model.access.csv` entries; a model without access rules is admin-only (Odoo warns in the log: `no access rules, consider adding one`).

## 8. Secure custom code (review checklist)

| Risk | Bad | Good |
|---|---|---|
| SQL injection | `cr.execute("... WHERE name = '%s'" % name)` | `cr.execute("... WHERE name = %s", [name])` or `odoo.tools.SQL` (17) |
| Privilege escalation | `sudo()` on user input, `auth='public'` routes calling `sudo().write()` | `sudo()` only for a specific, checked operation; check `self.env.user` rights |
| XSS | `t-raw` (deprecated) / `Markup(user_input)` / `fields.Html(sanitize=False)` | `t-out` with plain strings (auto-escaped); keep HTML sanitising on |
| Open redirect | `redirect(request.params['url'])` | allow only relative URLs |
| Secrets in code | API tokens in Python/XML or `ir.config_parameter` data files in git | environment / `server_environment` / secret store |
| Unsafe eval | `eval()` of user data | `odoo.tools.safe_eval` with minimal context |
| CSRF | `csrf=False` on state-changing `type='http'` POST routes | keep CSRF on; external callbacks verified by token/signature |

## 9. Secrets and data

- Backups are as sensitive as the database: encrypt off-site copies (e.g. `gpg`/`age`, or encrypted bucket), restrict access, delete old ones by policy.
- Restored copies: neutralise (crons, mail, payment providers) and replace production credentials with sandbox keys – https://2027.pp.ua/en/blog/odoo-stage-restore-stop-cron-jobs
- Personal data (GDPR/DSGVO): only needed users can export; delete test copies with real customer data when done.
- Secrets in git history are leaked even after deletion – rotate them.

## 10. Updates

- Odoo publishes security fixes into the stable branches: update the Odoo source/image regularly (e.g. monthly + on security advisories), then `-u` for changed modules – see https://2027.pp.ua/skill_odoo.md section 2.
- Also update: OCA modules, Python packages (`pip list --outdated` inside the image), PostgreSQL minor versions, OS packages, nginx.
- Subscribe to Odoo security advisories (odoo.com/security-report and the `odoo/odoo` GitHub security advisories).

## 11. Monitoring and incident response

Watch: failed logins per hour (log), new admin users (`res_users` + group_system), new API keys, `ir_cron`/`ir_actions_server` changes (code in server actions runs as sudo), unusual exports, disk/CPU spikes, TLS expiry.

Suspected compromise:
1. Cut access: maintenance page or IP allow-list at nginx; keep the server running for analysis (snapshot disk if possible).
2. Preserve evidence: Odoo log, nginx access log, `pg_dump` of the current state.
3. Check: admin users and groups, `res_users_apikeys`, server actions / automated actions / crons with Python code, recently modified views (`ir_ui_view` write_date), custom modules on disk (`git status`).
4. Reset: all admin passwords, all API keys, `admin_passwd`, DB password, SMTP/bank/shop credentials; ask users to change passwords (changing a password invalidates that user's other sessions).
5. Fix the entry point (patch, close port/route, remove module), then restore normal access; document what happened.

More (article with commands): secrets and phone numbers in URL query strings end up in access logs – log `$uri` only, tokens in headers; secret inventory and rotation; Docker ports bypass ufw (DOCKER-USER); PostgreSQL TLS (`ssl=on`, `hostssl`, `db_sslmode=verify-full`) or WireGuard between servers; auditd against insiders: https://2027.pp.ua/en/blog/odoo-server-security-logs-secrets-ports-encryption
