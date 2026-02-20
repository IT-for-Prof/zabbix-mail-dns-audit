# Autoconfig / Autodiscover DNS Monitoring — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add DNS presence checks for `autoconfig.<domain>`, `autodiscover.<domain>`, and `_autodiscover._tcp.<domain>` SRV to the existing audit script and Zabbix template.

**Architecture:** New `check_mail_client_config()` function added to `externalscripts/mail.dns.audit`; output appended to the existing JSON blob under `mail_client_config`; five new dependent items and three triggers (plus one DNS-error trigger enabling dependencies) added to `template_mail_dns_audit_zabbix.yaml`.

**Tech Stack:** Python 3 (dnspython), Zabbix 7.0 YAML template format.

**Design doc:** `docs/plans/2026-02-20-autoconfig-autodiscover-design.md`

---

## Task 1: Add `check_mail_client_config()` to the script

**Files:**
- Modify: `externalscripts/mail.dns.audit` (after `check_bimi()` function, approximately line 287)

**Step 1: Insert the new function**

Add this function after `check_bimi()` (after line ~287, before `check_ns_sync()`):

```python
def check_mail_client_config(resolver: dns.resolver.Resolver, domain: str) -> Dict:
    """
    Check DNS records for mail client autoconfiguration.
    Checks autoconfig.<domain> (A/CNAME), autodiscover.<domain> (A/CNAME),
    and _autodiscover._tcp.<domain> (SRV).
    Returns:
    {
      "autoconfig": {"present": bool, "type": str, "records": [...]},
      "autodiscover": {"present": bool, "type": str, "records": [...]},
      "autodiscover_srv": {"present": bool, "records": [...]}
    }
    type is "A", "CNAME", or "MISSING".
    """
    def _check_a_cname(host: str) -> Dict:
        cname_records, _, _ = query_records(resolver, host, "CNAME")
        if cname_records:
            return {"present": True, "type": "CNAME", "records": cname_records}
        a_records, _, _ = query_records(resolver, host, "A")
        if a_records:
            return {"present": True, "type": "A", "records": a_records}
        return {"present": False, "type": "MISSING", "records": []}

    autoconfig = _check_a_cname(f"autoconfig.{domain}")
    autodiscover = _check_a_cname(f"autodiscover.{domain}")
    srv_records, _, _ = query_records(resolver, f"_autodiscover._tcp.{domain}", "SRV")
    autodiscover_srv = {"present": bool(srv_records), "records": srv_records}

    return {
        "autoconfig": autoconfig,
        "autodiscover": autodiscover,
        "autodiscover_srv": autodiscover_srv,
    }
```

**Step 2: Call the function in `main()` and add to `result`**

In `main()`, find where `result["bimi"]` is set (approximately line 902) and add immediately after:

```python
        # Mail client autoconfiguration DNS records
        result["mail_client_config"] = check_mail_client_config(resolver, domain)
```

**Step 3: Add to the `simulate` block**

In the `simulated` dict (approximately line 679), add the new key alongside `"bimi"`:

```python
            "mail_client_config": {
                "autoconfig": {"present": False, "type": "MISSING", "records": []},
                "autodiscover": {"present": False, "type": "MISSING", "records": []},
                "autodiscover_srv": {"present": False, "records": []},
            },
```

**Step 4: Also add to `result` initialization block**

Find the `result = { ... }` dict near the top of `main()` (~line 751) and add:

```python
        "mail_client_config": {
            "autoconfig": {"present": False, "type": "MISSING", "records": []},
            "autodiscover": {"present": False, "type": "MISSING", "records": []},
            "autodiscover_srv": {"present": False, "records": []},
        },
```

**Step 5: Bump VERSION**

Change `VERSION = "0.1.21"` to `VERSION = "0.1.29"` at the top of the script.

**Step 6: Verify simulate output**

Run:
```bash
/c/Python314/python externalscripts/mail.dns.audit example.com --simulate | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('mail_client_config'), indent=2))"
```

Expected output:
```json
{
  "autoconfig": {"present": false, "type": "MISSING", "records": []},
  "autodiscover": {"present": false, "type": "MISSING", "records": []},
  "autodiscover_srv": {"present": false, "records": []}
}
```

**Step 7: Verify live against a known domain**

Run:
```bash
/c/Python314/python externalscripts/mail.dns.audit gmail.com | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('mail_client_config'), indent=2))"
```

Expected: `autoconfig` and/or `autodiscover` show `"present": true` with a CNAME record (Gmail uses `ghs.google.com` or similar for autoconfig).

**Step 8: Commit**

```bash
git add externalscripts/mail.dns.audit
git commit -m "feat: add autoconfig/autodiscover DNS checks (v0.1.29)"
```

---

## Task 2: Add 5 new dependent items to the Zabbix template

**Files:**
- Modify: `template_mail_dns_audit_zabbix.yaml`

Insert the following YAML block into the `items:` list, just before the `discovery_rules:` key (at the very end of the items list, after `mail.spf.multiple`). Note the indentation: items are indented 8 spaces under `items:`.

The master_item key to use in all items (copy exactly):
```
mail.dns.audit[{HOST.HOST},{$DNS_RESOLVER},{$DNS_TIMEOUT_SEC},{$CHECK_IPV6},{$DNSBL_ZONES},{$CIDR_ALLOWLIST},{$SPF_MAX_LOOKUPS},{$SPF_EXPECT_ALL},{$DNSBL_CACHE_TTL_SEC},{$MAX_MX_CHECK},{$DNSBL_MAX_IP},{$DKIM_SELECTORS},{$DNS_SHUFFLE}]
```

**Items to insert:**

```yaml
        - uuid: a1b2c3d4e5f64a7b8c9d0e1f2a3b4c5d
          name: 'Autoconfig DNS present'
          type: DEPENDENT
          key: mail.autoconfig.present
          delay: '0'
          description: '1 = autoconfig.<domain> resolves (A or CNAME), 0 = missing. Used by Thunderbird and Mozilla-compatible mail clients.'
          preprocessing:
            - type: JSONPATH
              parameters:
                - $.mail_client_config.autoconfig.present
              error_handler: CUSTOM_VALUE
              error_handler_params: 'false'
            - type: JAVASCRIPT
              parameters:
                - 'return (value===true || value=="true" || value=="1") ? 1 : 0;'
          master_item:
            key: 'mail.dns.audit[{HOST.HOST},{$DNS_RESOLVER},{$DNS_TIMEOUT_SEC},{$CHECK_IPV6},{$DNSBL_ZONES},{$CIDR_ALLOWLIST},{$SPF_MAX_LOOKUPS},{$SPF_EXPECT_ALL},{$DNSBL_CACHE_TTL_SEC},{$MAX_MX_CHECK},{$DNSBL_MAX_IP},{$DKIM_SELECTORS},{$DNS_SHUFFLE}]'
          tags:
            - tag: Application
              value: 'Mail DNS'
        - uuid: b2c3d4e5f6a74b8c9d0e1f2a3b4c5d6e
          name: 'Autoconfig DNS record type'
          type: DEPENDENT
          key: mail.autoconfig.type
          delay: '0'
          value_type: TEXT
          trends: '0'
          description: 'Record type for autoconfig.<domain>: A, CNAME, or MISSING.'
          preprocessing:
            - type: JSONPATH
              parameters:
                - $.mail_client_config.autoconfig.type
              error_handler: CUSTOM_VALUE
              error_handler_params: MISSING
          master_item:
            key: 'mail.dns.audit[{HOST.HOST},{$DNS_RESOLVER},{$DNS_TIMEOUT_SEC},{$CHECK_IPV6},{$DNSBL_ZONES},{$CIDR_ALLOWLIST},{$SPF_MAX_LOOKUPS},{$SPF_EXPECT_ALL},{$DNSBL_CACHE_TTL_SEC},{$MAX_MX_CHECK},{$DNSBL_MAX_IP},{$DKIM_SELECTORS},{$DNS_SHUFFLE}]'
          tags:
            - tag: Application
              value: 'Mail DNS'
        - uuid: c3d4e5f6a7b84c9d0e1f2a3b4c5d6e7f
          name: 'Autodiscover DNS present'
          type: DEPENDENT
          key: mail.autodiscover.present
          delay: '0'
          description: '1 = autodiscover.<domain> resolves (A or CNAME), 0 = missing. Used by Outlook and Exchange-compatible clients.'
          preprocessing:
            - type: JSONPATH
              parameters:
                - $.mail_client_config.autodiscover.present
              error_handler: CUSTOM_VALUE
              error_handler_params: 'false'
            - type: JAVASCRIPT
              parameters:
                - 'return (value===true || value=="true" || value=="1") ? 1 : 0;'
          master_item:
            key: 'mail.dns.audit[{HOST.HOST},{$DNS_RESOLVER},{$DNS_TIMEOUT_SEC},{$CHECK_IPV6},{$DNSBL_ZONES},{$CIDR_ALLOWLIST},{$SPF_MAX_LOOKUPS},{$SPF_EXPECT_ALL},{$DNSBL_CACHE_TTL_SEC},{$MAX_MX_CHECK},{$DNSBL_MAX_IP},{$DKIM_SELECTORS},{$DNS_SHUFFLE}]'
          tags:
            - tag: Application
              value: 'Mail DNS'
        - uuid: d4e5f6a7b8c94d0e1f2a3b4c5d6e7f8a
          name: 'Autodiscover DNS record type'
          type: DEPENDENT
          key: mail.autodiscover.type
          delay: '0'
          value_type: TEXT
          trends: '0'
          description: 'Record type for autodiscover.<domain>: A, CNAME, or MISSING.'
          preprocessing:
            - type: JSONPATH
              parameters:
                - $.mail_client_config.autodiscover.type
              error_handler: CUSTOM_VALUE
              error_handler_params: MISSING
          master_item:
            key: 'mail.dns.audit[{HOST.HOST},{$DNS_RESOLVER},{$DNS_TIMEOUT_SEC},{$CHECK_IPV6},{$DNSBL_ZONES},{$CIDR_ALLOWLIST},{$SPF_MAX_LOOKUPS},{$SPF_EXPECT_ALL},{$DNSBL_CACHE_TTL_SEC},{$MAX_MX_CHECK},{$DNSBL_MAX_IP},{$DKIM_SELECTORS},{$DNS_SHUFFLE}]'
          tags:
            - tag: Application
              value: 'Mail DNS'
        - uuid: e5f6a7b8c9d04e1f2a3b4c5d6e7f8a9b
          name: 'Autodiscover SRV present'
          type: DEPENDENT
          key: mail.autodiscover_srv.present
          delay: '0'
          description: '1 = _autodiscover._tcp.<domain> SRV record found, 0 = missing. SRV is the fallback autodiscover mechanism.'
          preprocessing:
            - type: JSONPATH
              parameters:
                - $.mail_client_config.autodiscover_srv.present
              error_handler: CUSTOM_VALUE
              error_handler_params: 'false'
            - type: JAVASCRIPT
              parameters:
                - 'return (value===true || value=="true" || value=="1") ? 1 : 0;'
          master_item:
            key: 'mail.dns.audit[{HOST.HOST},{$DNS_RESOLVER},{$DNS_TIMEOUT_SEC},{$CHECK_IPV6},{$DNSBL_ZONES},{$CIDR_ALLOWLIST},{$SPF_MAX_LOOKUPS},{$SPF_EXPECT_ALL},{$DNSBL_CACHE_TTL_SEC},{$MAX_MX_CHECK},{$DNSBL_MAX_IP},{$DKIM_SELECTORS},{$DNS_SHUFFLE}]'
          tags:
            - tag: Application
              value: 'Mail DNS'
```

**Step 1: Insert the items block**

Open `template_mail_dns_audit_zabbix.yaml`. Find the last item in the `items:` list (the `mail.spf.multiple` item ending around line 1005) and the `discovery_rules:` key that follows it. Insert the 5-item block between them.

**Step 2: Verify YAML is valid**

```bash
/c/Python314/python -c "import yaml; yaml.safe_load(open(r'template_mail_dns_audit_zabbix.yaml', encoding='utf-8')); print('YAML OK')"
```

Expected: `YAML OK`

**Step 3: Commit**

```bash
git add template_mail_dns_audit_zabbix.yaml
git commit -m "feat: add autoconfig/autodiscover dependent items to Zabbix template"
```

---

## Task 3: Add DNS script error trigger (prerequisite for dependencies)

**Files:**
- Modify: `template_mail_dns_audit_zabbix.yaml`

The `mail.dns.error` item (around line 341) currently has no triggers section. Add one.

Find this section:
```yaml
          tags:
            - tag: Application
              value: 'Mail DNS'
        - uuid: 1af104976a02494da0fdc8758fccb868
          name: 'DNS query time ms'
```

Replace with:
```yaml
          tags:
            - tag: Application
              value: 'Mail DNS'
          triggers:
            - uuid: f6a7b8c9d0e14f2a3b4c5d6e7f8a9b0c
              expression: 'length(last(/Template Mail DNS Audit Zabbix/mail.dns.error))>0'
              name: 'DNS audit script error on {HOST.HOST}'
              priority: HIGH
              description: 'The mail DNS audit script returned an error message. Check Zabbix server connectivity to the external script, DNS resolver availability, and script configuration.'
              tags:
                - tag: Application
                  value: 'Mail DNS'
                - tag: component
                  value: mail-dns
        - uuid: 1af104976a02494da0fdc8758fccb868
          name: 'DNS query time ms'
```

**Step 1: Make the edit** (insert triggers block into `mail.dns.error` item).

**Step 2: Verify YAML**

```bash
/c/Python314/python -c "import yaml; yaml.safe_load(open(r'template_mail_dns_audit_zabbix.yaml', encoding='utf-8')); print('YAML OK')"
```

**Step 3: Commit**

```bash
git add template_mail_dns_audit_zabbix.yaml
git commit -m "feat: add DNS script error trigger to enable trigger dependencies"
```

---

## Task 4: Add 3 new autoconfiguration triggers with dependencies

**Files:**
- Modify: `template_mail_dns_audit_zabbix.yaml`

Add triggers to two of the new items added in Task 2:
- T1 goes under `mail.autoconfig.present` item
- T2 goes under `mail.autodiscover.present` item
- T3 goes under `mail.autodiscover_srv.present` item

The dependency expression for all three is:
```
length(last(/Template Mail DNS Audit Zabbix/mail.dns.error))>0
```

**Step 1: Add T1 trigger to `mail.autoconfig.present` item**

Find the `mail.autoconfig.present` item's `tags:` section and add triggers after it:

```yaml
          tags:
            - tag: Application
              value: 'Mail DNS'
          triggers:
            - uuid: a7b8c9d0e1f24a3b4c5d6e7f8a9b0c1d
              expression: 'last(/Template Mail DNS Audit Zabbix/mail.autoconfig.present)=0'
              name: 'Autoconfig DNS missing for {HOST.HOST}'
              priority: INFO
              description: 'autoconfig.{HOST.HOST} A/CNAME record not found. Thunderbird and other Mozilla-compatible mail clients will not be able to auto-discover mail server settings.'
              dependencies:
                - name: 'DNS audit script error on {HOST.HOST}'
                  expression: 'length(last(/Template Mail DNS Audit Zabbix/mail.dns.error))>0'
                  recovery_expression: ''
              tags:
                - tag: Application
                  value: 'Mail DNS'
                - tag: component
                  value: mail-dns
```

**Step 2: Add T2 trigger to `mail.autodiscover.present` item**

Same pattern on the `mail.autodiscover.present` item:

```yaml
          tags:
            - tag: Application
              value: 'Mail DNS'
          triggers:
            - uuid: b8c9d0e1f2a34b4c5d6e7f8a9b0c1d2e
              expression: 'last(/Template Mail DNS Audit Zabbix/mail.autodiscover.present)=0'
              name: 'Autodiscover DNS missing for {HOST.HOST}'
              priority: INFO
              description: 'autodiscover.{HOST.HOST} A/CNAME record not found. Outlook and Exchange-compatible clients will not be able to auto-discover mail server settings.'
              dependencies:
                - name: 'DNS audit script error on {HOST.HOST}'
                  expression: 'length(last(/Template Mail DNS Audit Zabbix/mail.dns.error))>0'
                  recovery_expression: ''
              tags:
                - tag: Application
                  value: 'Mail DNS'
                - tag: component
                  value: mail-dns
```

**Step 3: Add T3 trigger to `mail.autodiscover_srv.present` item**

T3 fires only when ALL three mechanisms are simultaneously absent:

```yaml
          tags:
            - tag: Application
              value: 'Mail DNS'
          triggers:
            - uuid: c9d0e1f2a3b44c5d6e7f8a9b0c1d2e3f
              expression: 'last(/Template Mail DNS Audit Zabbix/mail.autoconfig.present)=0 and last(/Template Mail DNS Audit Zabbix/mail.autodiscover.present)=0 and last(/Template Mail DNS Audit Zabbix/mail.autodiscover_srv.present)=0'
              name: 'No mail client autoconfiguration for {HOST.HOST}'
              priority: WARNING
              description: 'None of the standard mail client autoconfiguration DNS mechanisms are present (autoconfig A/CNAME, autodiscover A/CNAME, _autodiscover._tcp SRV). Mail clients will fall back to manual configuration or ISP database lookup.'
              dependencies:
                - name: 'DNS audit script error on {HOST.HOST}'
                  expression: 'length(last(/Template Mail DNS Audit Zabbix/mail.dns.error))>0'
                  recovery_expression: ''
              tags:
                - tag: Application
                  value: 'Mail DNS'
                - tag: component
                  value: mail-dns
```

**Step 4: Verify YAML**

```bash
/c/Python314/python -c "import yaml; yaml.safe_load(open(r'template_mail_dns_audit_zabbix.yaml', encoding='utf-8')); print('YAML OK')"
```

**Step 5: Count triggers to confirm correct total**

```bash
/c/Python314/python -c "
import yaml
data = yaml.safe_load(open(r'template_mail_dns_audit_zabbix.yaml', encoding='utf-8'))
tmpl = data['zabbix_export']['templates'][0]
count = 0
for item in tmpl.get('items', []):
    count += len(item.get('triggers', []))
for dr in tmpl.get('discovery_rules', []):
    for item in dr.get('item_prototypes', []):
        count += len(item.get('trigger_prototypes', []))
print('Total triggers:', count)
"
```

Expected: `Total triggers: 22` (was 18, added 4: DNS error + T1 + T2 + T3)

**Step 6: Commit**

```bash
git add template_mail_dns_audit_zabbix.yaml
git commit -m "feat: add autoconfig/autodiscover triggers with DNS error dependencies"
```

---

## Task 5: Update template description and version

**Files:**
- Modify: `template_mail_dns_audit_zabbix.yaml` (description block at top, line ~10)
- Modify: `CHANGELOG.md`

**Step 1: Update template description**

In the template `description:` block, change:
- `Version: 0.1.28` → `Version: 0.1.29`
- Add `- Mail client autoconfiguration DNS (autoconfig, autodiscover, SRV)` to the Monitors list

**Step 2: Update CHANGELOG.md**

Add an entry at the top of CHANGELOG.md:

```markdown
## [0.1.29] - 2026-02-20

### Added
- `check_mail_client_config()` in `mail.dns.audit`: DNS presence checks for `autoconfig.<domain>` (A/CNAME), `autodiscover.<domain>` (A/CNAME), and `_autodiscover._tcp.<domain>` (SRV).
- Five new dependent Zabbix items: `mail.autoconfig.present`, `mail.autoconfig.type`, `mail.autodiscover.present`, `mail.autodiscover.type`, `mail.autodiscover_srv.present`.
- Three new triggers: autoconfig missing (INFO), autodiscover missing (INFO), no autoconfiguration at all (WARNING).
- New DNS script error trigger (`mail.dns.error` non-empty → HIGH) used as dependency to suppress autoconfiguration alerts during script failures.
```

**Step 3: Commit**

```bash
git add template_mail_dns_audit_zabbix.yaml CHANGELOG.md
git commit -m "docs: update version to 0.1.29, update CHANGELOG for autoconfig/autodiscover"
```
