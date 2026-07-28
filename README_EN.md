# Zabbix Mail DNS Audit

![Zabbix 7.0+](https://img.shields.io/badge/Zabbix-7.0%2B-blue)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-green)

Monitor email domain infrastructure in Zabbix: MX, SPF, DMARC, DKIM, DNSBL, DNSSEC, PTR/FCrDNS for MX.

**Author:** itforprof.com by Konstantin Tyutyunnik

## About

Zabbix Mail DNS Audit is an integrated solution for auditing email domain DNS configuration:

- **Python3 script** for DNS record checking
- **Zabbix 7.0 template** with pre-configured items, triggers and dashboard
- **Automatic discovery** of MX hosts and DNSBL zones via LLD
- **Result caching** for load optimization
- **Fallback mechanism** when public resolvers are blocked

## Features

- ✅ MX record checking and TTL monitoring
- ✅ SPF analysis (RFC 7208), lookup counting
- ✅ DMARC policy monitoring
- ✅ DKIM key tracking and RSA key size validation (alerts on keys < 2048 bits or ≤ 1024 bits)
- ✅ DMARC alignment mode detection (adkim/aspf: relaxed or strict)
- ✅ MX → CNAME violation detection (RFC 5321 §5 prohibits CNAME as MX target)
- ✅ DNSBL checking (statuses: LISTED, NOT LISTED, POLICY/ERROR, CHECK FAILED)
- ✅ DNSSEC validation (DS records, AD flags)
- ✅ PTR/FCrDNS checks for MX (missing PTR, FCrDNS mismatch, generic PTR)
- ✅ Transport security: MTA-STS and TLS-RPT
- ✅ BIMI (presence of TXT default._bimi)
- ✅ Authoritative NS consistency (SOA serial)
- ✅ Extended DMARC triggers (p=none, pct<100) and SPF (+all, ?all)
- ✅ DNS performance monitoring (threshold {$DNS_SLOW_MS})
- ✅ IPv6 support (optional)
- ✅ Multiple DNS resolvers with shuffling
- ✅ Local result caching
- ✅ Mail client autoconfiguration DNS checks (autoconfig, autodiscover, SRV)
- ✅ Change detection with before→after display: SPF, MX, DKIM and DMARC change triggers show old→new values in the Problems list Info column (Zabbix operational data)

- ✅ Duplicate records: MX, DMARC, DKIM selectors, NS, SOA (two DMARC records disable the policy entirely per RFC 7489)
- ✅ Null MX (RFC 7505): a domain that has switched mail off is named directly instead of being reported as missing MX
- ✅ Revoked DKIM key (empty `p=`) and testing mode `t=y` (RFC 6376 section 3.6.1) — the record is present while the protection is not
- ✅ Nameservers not answering SOA: a silent member of the delegation is invisible to the serial-consistency check
- ✅ Per-section visibility flags: an absence check may claim "the record is missing" only when its own lookups answered
- ✅ Per-address, per-MX-host, per-selector and per-nameserver discovery: PTR status, CNAME, key size, SOA serial
- ✅ Addresses left outside the blocklist check are surfaced separately — "not checked" must not read as "clean"
- ✅ NS and DS record changes with before→after display

## Requirements

- Zabbix 7.0+
- Python 3.11+ in a dedicated environment at `/opt/zabbix-mail-dns/venv` (see step 1)
- dnspython 2.6+ (installed into that environment)
- Linux/Unix environment
- Internet access for DNS and DNSBL queries

> **Why a venv rather than the system Python.** The check runs on proxies, and proxies
> come from different generations: on one machine the system interpreter is still
> Python 3.6, which has no `ipaddress.subnet_of()`. A dedicated environment at the same
> path gives every machine one interpreter and one dnspython version, so the script stays
> byte-identical everywhere and its behaviour stays reproducible.

## Quick Start

### Step 1: Python environment

Identical on the Zabbix server and on every proxy that executes the check:

```bash
# Pick the newest interpreter available
best=""; for v in 3.13 3.12 3.11; do [ -x /usr/bin/python$v ] && { best=$v; break; }; done

mkdir -p /opt/zabbix-mail-dns
/usr/bin/python$best -m venv /opt/zabbix-mail-dns/venv
/opt/zabbix-mail-dns/venv/bin/pip install --upgrade pip
/opt/zabbix-mail-dns/venv/bin/pip install "dnspython>=2.6"
chown -R zabbix:zabbix /opt/zabbix-mail-dns
```

Verify:

```bash
/opt/zabbix-mail-dns/venv/bin/python3 -c "import sys, dns; print(sys.version, dns.__version__)"
```

The script's shebang points at this environment, so the system Python is never used and
distribution package conflicts (PEP 668, `externally-managed-environment`) cannot occur.

### Step 2: Deploy Script

Choose one of three options:

#### Option A: Git (full clone)

```bash
git clone https://github.com/IT-for-Prof/zabbix-mail-dns-audit.git
cd zabbix-mail-dns-audit
cp externalscripts/mail.dns.audit /usr/lib/zabbix/externalscripts/
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

#### Option B: wget (direct script download)

```bash
# Download script directly to Zabbix
wget -O /usr/lib/zabbix/externalscripts/mail.dns.audit \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/externalscripts/mail.dns.audit

# Set permissions
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

#### Option C: curl (alternative download)

```bash
# Download script via curl
curl -L https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/externalscripts/mail.dns.audit \
  -o /usr/lib/zabbix/externalscripts/mail.dns.audit

# Set permissions
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

#### Verify Script Installation

```bash
# Check file exists
ls -l /usr/lib/zabbix/externalscripts/mail.dns.audit

# Check dependencies (script version, Python, dnspython)
/usr/lib/zabbix/externalscripts/mail.dns.audit --selfcheck

# Test functionality
/usr/lib/zabbix/externalscripts/mail.dns.audit example.com 8.8.8.8 3
```

> **Zabbix Proxy:** If hosts are monitored by a **Zabbix Proxy**, deploy the script and Python dependencies on the **proxy server** — not the Zabbix Server. External check items run on whichever machine (server or proxy) monitors the host. The same installation steps apply to each proxy. Run `--selfcheck` on each machine after install.

> **Execution timeout:** the script caps its total runtime with a deadline (default 25s, env `MAIL_DNS_DEADLINE_SEC`) that must stay **below** the Zabbix external-check timeout, so a stuck resolver yields a clear `meta.error` instead of "Timeout while executing a shell script".
>
> **You must raise that timeout by hand.** The Zabbix default for external checks is **3 seconds** (range 1-30), not 30. A typical run takes about 5 seconds, so on the default the poller kills the script long before the deadline fires and you never see the error envelope. Set the external-check timeout to 30s (*Administration → General → Timeouts*) and keep `MAIL_DNS_DEADLINE_SEC ≈ Timeout − 5`. A proxy's value overrides the global one and an item's value overrides both; the check runs on the proxy, so that is where it has to be raised.

### Step 3: Download Template and Import

**Option A: Git (already downloaded)**

```bash
# Template is already in cloned repository
ls template_mail_dns_audit_zabbix.yaml
```

**Option B: wget (download template)**

```bash
# Download template for import
wget -O /tmp/template_mail_dns_audit_zabbix.yaml \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/template_mail_dns_audit_zabbix.yaml
```

**Option C: curl (download template)**

```bash
# Download template via curl
curl -L https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/template_mail_dns_audit_zabbix.yaml \
  -o /tmp/template_mail_dns_audit_zabbix.yaml
```

**Import to Zabbix:**

1. Open Zabbix web interface
2. Admin → Templates
3. Click Import
4. Select file `template_mail_dns_audit_zabbix.yaml`
5. Click Import

### Step 4: Create Host for Monitoring

1. Data Collection → Hosts
2. Create Host
3. Fill in:
   - Host name: `example.com` (or domain name)
   - Visible name: display name
   - Groups: select group
   - Interfaces: `127.0.0.1` (placeholder — external check items do not use the interface)
4. Go to Templates tab
5. Add `Template Mail DNS Audit Zabbix`
6. Create

## Update

### Step 1: Update Script

```bash
wget -O /usr/lib/zabbix/externalscripts/mail.dns.audit \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/externalscripts/mail.dns.audit
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

> **Zabbix Proxy:** Update the script on **every proxy server** where it is deployed.

### Step 2: Update Template

```bash
wget -O /tmp/template_mail_dns_audit_zabbix.yaml \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/template_mail_dns_audit_zabbix.yaml
```

Import to Zabbix: Data collection → Templates → Import → select file → Import.

### Step 3: Verify Version

After update, the `Script version mismatch` trigger should disappear. If it persists — the script on the server or proxy was not updated.

```bash
# Check script version
/usr/lib/zabbix/externalscripts/mail.dns.audit --version
```

## Configuration

All parameters are configured via template macros in Zabbix:

### Network Parameters

| Macro | Value | Description |
|-------|-------|-------------|
| `{$DNS_RESOLVER}` | (empty) | Resolver IPs (comma-separated). Empty = system |
| `{$DNS_TIMEOUT_SEC}` | `10` | Timeout for a single DNS query (seconds). This is the cost of one hung lookup: at 3s a transient failure was short enough to look like an authoritative "no such record" |
| `{$DNS_SHUFFLE}` | `1` | Shuffle resolvers (1/0) |
| `{$DNS_SLOW_MS}` | `12000` | Slow DNS threshold (ms). Must exceed `{$DNS_TIMEOUT_SEC}`, otherwise the trigger degenerates into a duplicate of "one lookup timed out" |

### SPF and Checks

| Macro | Value | Description |
|-------|-------|-------------|
| `{$SPF_MAX_LOOKUPS}` | `10` | Maximum lookups for SPF |
| `{$SPF_EXPECT_ALL}` | `-all\|~all` | Regex for "all" mechanism |
| `{$CIDR_ALLOWLIST}` | (empty) | Allowed CIDR for SPF |

### DNSBL Parameters

| Macro | Value | Description |
|-------|-------|-------------|
| `{$DNSBL_ZONES}` | `zen.spamhaus.org,b.barracudacentral.org` | Zones to check. Barracuda requires free registration of the querying IPs |
| `{$DNSBL_TEST_IP}` | `127.0.0.2` | Canary address: a live blocklist must return it. Empty disables the self-test |
| `{$DNSBL_CACHE_TTL_SEC}` | `1200` | DNSBL cache TTL (seconds) |
| `{$DNSBL_MAX_IP}` | `5` | Max IPs for DNSBL (`0` means no limit) |
| `{$MAX_MX_CHECK}` | `5` | Max MX to check |

### Check Control

Per-host opt-in/opt-out macros. Set at the host level to override the template default.

| Macro | Default | Description |
|-------|---------|-------------|
| `{$CHECK_BIMI}` | `1` | Set to `0` to suppress BIMI record missing alert |
| `{$CHECK_DMARC_RUA}` | `0` | Set to `1` to alert when DMARC is present but `rua=` is absent (opt-in — `rua=` is optional per RFC 7489) |
| `{$CHECK_DNSSEC}` | `1` | Set to `0` to suppress DNSSEC AD flag and DS record alerts |
| `{$CHECK_MTA_STS}` | `1` | Set to `0` to suppress MTA-STS record missing alert |
| `{$CHECK_TLS_RPT}` | `1` | Set to `0` to suppress TLS-RPT record missing alert |
| `{$MAIL_CLIENT_AUTOCONFIG_CHECK}` | `1` | Set to `0` to suppress autoconfig/autodiscover alerts |
| `{$SPF_CHECK_MX_COVERAGE}` | `1` | Set to `0` to suppress "MX not covered by SPF" alert |

### Other

| Macro | Value | Description |
|-------|-------|-------------|
| `{$CHECK_IPV6}` | `0` | Check AAAA records (1/0) |
| `{$DKIM_SELECTORS}` | `default` | DKIM selectors (comma-separated, without `._domainkey`) |
| `{$TEMPLATE_VERSION}` | `0.1.61` | Template version. Must match `VERSION` in the script, otherwise the version-mismatch warning fires |
| `{$MAIL_DNS_NODATA_SEC}` | `3h` | nodata threshold for the master item. Must exceed twice the poll interval: at an hourly poll the old `1800` was true for half of every hour and the trigger flapped permanently |

### Visibility and coverage

| Macro | Purpose |
|---|---|
| `{$MAIL_DNS_NODATA_SEC}` | Silence window before the "script not running" alert. Must exceed twice the polling interval: at an hourly poll a 30-minute window is true for half of every hour. Zabbix does not evaluate periods under 30 seconds. |
| `{$DNSBL_MAX_IP}` | How many addresses to check against blocklists. PTR and FCrDNS run for **every** address regardless of this limit — reverse DNS has no external quota. Whatever is left out is counted by `mail.dnsbl.not_checked`. |
| `{$CIDR_ALLOWLIST}` | Networks allowed to appear in SPF. An empty value switches the comparison off; malformed `ip4:`/`ip6:` mechanisms are counted separately and always reported. |

## Usage

### Test Script Manually

```bash
# Basic check
./externalscripts/mail.dns.audit example.com

# With resolver specified
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0

# With full parameters
./externalscripts/mail.dns.audit example.com \
  "8.8.8.8" \           # resolver
  "3" \                 # timeout_sec
  "0" \                 # check_ipv6
  "zen.spamhaus.org" \  # dnsbl_zones
  "" \                  # cidr_allowlist
  "10" \                # spf_max_lookups
  "-all|~all" \         # spf_expect_all
  "1200" \              # dnsbl_cache_ttl
  "5" \                 # max_mx
  "1" \                 # dnsbl_max_ip
  "default" \           # dkim_selectors
  "1"                   # shuffle_resolvers
```

### Results in Zabbix

- **Latest Data**: view items (mail.mx.count, mail.spf.status, mail.dnsbl.* etc)
- **Triggers**: configured alerts for issues (missing MX, DNSBL, slow DNS, nodata for master item)
- **Duplicate checks**: flags and triggers for duplicates of MX, DMARC, DKIM selectors, NS, SOA
- **Dashboard**: "Mail DNS Audit Overview" displays overall status

## Testing

### Test suite and linter

```bash
# All four test files. Each is a standalone script; exit 1 on any mismatch
python3 tests/test_wave1_contracts.py
python3 tests/test_ptr_states.py
python3 tests/test_dnsbl_states.py
python3 tests/test_template_contracts.py

# Linter (rules F and E9; .ruff.toml includes the extensionless script)
ruff check .
```

> **Which interpreter.** `test_template_contracts.py` parses the template YAML and needs
> PyYAML, which the runtime environment `/opt/zabbix-mail-dns/venv` deliberately does not
> carry — it holds only dnspython, because the script itself needs nothing else. So run
> the tests with the **system** `python3`, not the environment's interpreter. That same
> file compiles every JavaScript preprocessing step from the template through `node`, so
> `node` must be installed for it.

### Built-in Simulations

```bash
# Simulate bad SPF
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0 \
  "zen.spamhaus.org" "" "10" "-all|~all" "1200" "5" "5" "default" "1" \
  --simulate bad_spf

# Simulate DNSBL
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0 \
  "zen.spamhaus.org" "" "10" "-all|~all" "1200" "5" "5" "default" "1" \
  --simulate dnsbl
```

### DNSBL Self-Test

```bash
# Check test IP status in DNSBL
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0 \
  "zen.spamhaus.org,b.barracudacentral.org" "" "10" "-all|~all" "1200" "5" "5" "default" "1" \
  --dnsbl-test-ip 127.0.0.2
```

### Debug

```bash
# Enable debug output
DEBUG_DNSBL=1 ./externalscripts/mail.dns.audit example.com
```

## Troubleshooting

### The script will not start: no interpreter or no dnspython

All three former cases — `externally-managed-environment` (PEP 668), a missing Python 3
of the required version, and a missing dnspython — are answered by the same thing: the
environment from step 1. Check that it is in place:

```bash
ls -l /opt/zabbix-mail-dns/venv/bin/python3
/usr/lib/zabbix/externalscripts/mail.dns.audit --selfcheck
```

`--selfcheck` prints the script version, the Python version and the dnspython version. If
the environment is missing, Zabbix receives a structured error in `meta.error` rather than
an empty reply, and the "DNS audit script error" trigger fires.

### DNSBL: "POLICY/ERROR" Status

Public resolvers (8.8.8.8) are blocked by DNSBL providers. Solution:

1. Install local resolver (Unbound/Bind) on local machine
2. Set macro: `{$DNS_RESOLVER} = "127.0.0.1"`

### DNSBL: a zone "cannot prove it is alive"

The verdict of a blocklist is its `A` answer; the `TXT` record only explains that verdict
in words. A zone that answers `A` is alive even when its `TXT` lookup times out — since
0.1.61 the script classifies by `A` alone and keeps the TXT error text in the `txt` field
for reading. So `mail.dnsbl.canary.failed` above zero now means the zone really did not
return `{$DNSBL_TEST_IP}`: it has been emptied (SORBS after 2024) or it refuses your
queries.

A slow `TXT` still costs wall-clock, and `zen.spamhaus.org` is the usual source of it:
public mirrors rate-limit. If runs creep toward `MAIL_DNS_DEADLINE_SEC`, lower
`{$DNS_TIMEOUT_SEC}` or move to a Spamhaus DQS key.

### Zabbix Proxy: Script Not Working

External check items run on the **proxy** that monitors the host, not the Zabbix Server. If the item shows "not supported" on a proxy-monitored host:

1. Deploy the script on each proxy server:
```bash
# Run on the proxy machine
wget -O /usr/lib/zabbix/externalscripts/mail.dns.audit \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/externalscripts/mail.dns.audit
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

2. Install Python and dnspython on the proxy (same steps as for the server above).

3. Verify the proxy's `ExternalScripts` path in `zabbix_proxy.conf` matches `/usr/lib/zabbix/externalscripts/`.

4. Test from the proxy machine:
```bash
su - zabbix -c "/usr/lib/zabbix/externalscripts/mail.dns.audit example.com"
```

### Script Not Executing from Zabbix

```bash
# Check permissions
ls -l /usr/lib/zabbix/externalscripts/mail.dns.audit

# Permissions should be 755, owner zabbix:zabbix
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit

# Test as zabbix user
su - zabbix -c "/usr/lib/zabbix/externalscripts/mail.dns.audit example.com"
```

## Architecture

### Data Flow

```
Zabbix Server (or Proxy, if host is proxy-monitored)
    ↓
mail.dns.audit (Master Item — External Check)
    ↓
Python script (externalscripts/mail.dns.audit)
    ├→ Get MX records
    ├→ Get SPF/DMARC/DKIM
    ├→ Analyze SPF mechanisms
    ├→ Check DNSBL zones
    └→ Verify DNSSEC
    ↓
JSON result + cache
    ↓
LLD Discovery (automatic discovery)
    ├→ mail.mx[{#MXHOST}]
    ├→ mail.dnsbl[{#DNSBL_IP}][{#DNSBL_ZONE}]
    └→ Dependent items
    ↓
Triggers & Alerts
```

### Caching

- DNSBL results stored in `/tmp/mail_dns_audit_cache.json` on the machine running the script (Zabbix Server or Proxy)
- TTL managed by macro `{$DNSBL_CACHE_TTL_SEC}` (default 1200 sec)
- Cache speeds up repeated checks and reduces load

## Changelog

Full history with rationale: [CHANGELOG.md](CHANGELOG.md)

## Links

- GitHub: https://github.com/IT-for-Prof/zabbix-mail-dns-audit
- Website: https://itforprof.com
- Issues: https://github.com/IT-for-Prof/zabbix-mail-dns-audit/issues

