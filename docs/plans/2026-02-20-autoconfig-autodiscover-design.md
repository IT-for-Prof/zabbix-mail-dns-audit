# Design: Autoconfig / Autodiscover DNS Monitoring

**Date:** 2026-02-20
**Scope:** DNS-only presence checks for mail client autoconfiguration records
**Approach:** Inline into existing `mail.dns.audit` script (Approach A)

---

## Background

Mail clients (Thunderbird, Outlook, Apple Mail) use DNS subdomains to auto-discover server settings:

- `autoconfig.<domain>` — Mozilla/Thunderbird standard (A or CNAME)
- `autodiscover.<domain>` — Microsoft/Exchange standard (A or CNAME)
- `_autodiscover._tcp.<domain>` — SRV fallback for autodiscover

If none of these records exist, mail clients fall back to manual configuration or ISP databases, degrading the user experience. This feature adds DNS presence monitoring for all three mechanisms.

---

## Script Changes (`externalscripts/mail.dns.audit`)

Add a new function `check_mail_client_config(resolver, domain)` that performs 5 DNS queries:

| Query | Record type | Detected |
|-------|-------------|---------|
| `autoconfig.<domain>` | A | Direct IP |
| `autoconfig.<domain>` | CNAME | Alias |
| `autodiscover.<domain>` | A | Direct IP |
| `autodiscover.<domain>` | CNAME | Alias |
| `_autodiscover._tcp.<domain>` | SRV | Service locator |

For A/CNAME queries: if CNAME resolves, type is `"CNAME"`; if A resolves (and no CNAME), type is `"A"`; if neither, type is `"MISSING"` and present is `false`.

### JSON output (new key `mail_client_config`)

```json
"mail_client_config": {
  "autoconfig": {
    "present": true,
    "type": "CNAME",
    "records": ["mail.example.com."]
  },
  "autodiscover": {
    "present": true,
    "type": "CNAME",
    "records": ["autodiscover.outlook.com."]
  },
  "autodiscover_srv": {
    "present": false,
    "records": []
  }
}
```

`type` values: `"A"` | `"CNAME"` | `"MISSING"`. SRV has no type field.

The function uses the same `resolver` instance and `query_records()` helper as all other checks — no new dependencies.

---

## Zabbix Template Changes

### New dependent items (5 total)

All dependent on the master item `mail.dns.audit[...]`.

| Item key | JSONPath | Value type | Purpose |
|----------|----------|-----------|---------|
| `mail.autoconfig.present` | `$.mail_client_config.autoconfig.present` | Boolean (0/1) | autoconfig DNS resolvable |
| `mail.autoconfig.type` | `$.mail_client_config.autoconfig.type` | Text | Record type: A, CNAME, or MISSING |
| `mail.autodiscover.present` | `$.mail_client_config.autodiscover.present` | Boolean (0/1) | autodiscover DNS resolvable |
| `mail.autodiscover.type` | `$.mail_client_config.autodiscover.type` | Text | Record type: A, CNAME, or MISSING |
| `mail.autodiscover_srv.present` | `$.mail_client_config.autodiscover_srv.present` | Boolean (0/1) | SRV record present |

The `type` items carry no triggers — they provide context when alerts fire.

### New triggers (3 total)

| ID | Name | Expression | Severity |
|----|------|-----------|---------|
| T1 | `autoconfig DNS missing for {HOST.HOST}` | `last(/mail.autoconfig.present)=0` | INFO |
| T2 | `autodiscover DNS missing for {HOST.HOST}` | `last(/mail.autodiscover.present)=0` | INFO |
| T3 | `No mail client autoconfiguration for {HOST.HOST}` | `last(/mail.autoconfig.present)=0 and last(/mail.autodiscover.present)=0 and last(/mail.autodiscover_srv.present)=0` | WARNING |

### Trigger dependency chain

```
DNS script error (HIGH)  [existing trigger: mail.dns.error not empty]
    suppresses:
    ├── T1: autoconfig missing (INFO)
    ├── T2: autodiscover missing (INFO)
    └── T3: No autoconfiguration at all (WARNING)
```

- T1 and T2 are independent — either can fire alone
- T3 fires only when all three mechanisms are simultaneously absent (real user impact)
- All three are suppressed by the existing DNS error trigger to avoid noise from script/resolver failures

---

## Out of Scope

- HTTP/HTTPS endpoint reachability checks
- XML content validation
- SRV record triggers (SRV absence alone is not actionable — A/CNAME are primary)
