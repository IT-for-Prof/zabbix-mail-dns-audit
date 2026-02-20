# CLAUDE.md — Project Rules

## UUID Generation

**Never hand-craft UUIDs.** Always generate proper UUIDv4:

```bash
python3 -c "import uuid; print(uuid.uuid4().hex)"
```

Zabbix API strictly validates UUIDs:
- Version nibble (character 13) must be `4`
- Variant nibble (character 17) must be `8`, `9`, `a`, or `b`

Invalid UUIDs like `a1b2c3d4e5f64a7b8c9d0e1f2a3b4c5d` will cause:
`Invalid parameter "/1/...": UUIDv4 is expected.`

## Zabbix Template Rules

- **Do not include `groups` in `configuration.import` rules** — removed in Zabbix 7.0 API; causes import failure.
- **Large template payloads (>~50KB)** must be sent from inside the container, not from the host:
  ```bash
  docker exec -i zabbix-zabbix-web-1 curl -s -X POST http://localhost:8080/api_jsonrpc.php ...
  ```
- Template version macro is `{$TEMPLATE_VERSION}` — bump it on every release.

## Script Deployment

- Script path on host: `/opt/zabbix/externalscripts/mail.dns.audit`
- Mounted read-only into container at: `/usr/lib/zabbix/externalscripts/`
- After copying: `chmod 755` and `chown zabbix:zabbix`
- Zabbix server address: `172.19.251.154` (WSL AlmaLinux-9 — this IS the server)
- Zabbix API URL (inside container): `http://zabbix-server:8080`
- Zabbix web container name: `zabbix-zabbix-web-1`

## Versioning

- Script and template share the same version number (e.g., `0.1.29`)
- Bump `VERSION` constant in `externalscripts/mail.dns.audit`
- Bump `{$TEMPLATE_VERSION}` macro value in `template_mail_dns_audit_zabbix.yaml`
- Add entry to `CHANGELOG.md` under a new `## [x.y.z] - YYYY-MM-DD` heading
- Update `{$TEMPLATE_VERSION}` value in both `README.md` and `README_EN.md`
- Add entry to "Recent updates" / "Последние обновления" in both READMEs

## Git

- Main branch: `main`
- Commit docs separately from code/template changes
- Always push after release commits
