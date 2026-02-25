# Zabbix Mail DNS Audit

![Zabbix 7.0+](https://img.shields.io/badge/Zabbix-7.0%2B-blue)
![Python 3.6+](https://img.shields.io/badge/Python-3.6%2B-green)

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

## Requirements

- Zabbix 7.0+
- Python 3.6+
- dnspython 2.0+
- Linux/Unix environment
- Internet access for DNS and DNSBL queries

## Quick Start

### Step 1: Install Dependencies

#### Ubuntu/Debian 12+ and Python 3.11+ (PEP 668)

Starting with Debian 12/Ubuntu 23.10, the system protects global Python from modification via pip. Use one of the methods:

**Method A: Virtual environment**

```bash
apt update
apt install -y python3-full python3-venv

mkdir -p /opt/zabbix-dns-monitoring
python3 -m venv /opt/zabbix-dns-monitoring/.venv
/opt/zabbix-dns-monitoring/.venv/bin/pip install -U pip dnspython
```

> **⚠️ Zabbix compatibility:** The script shebang is `#!/usr/bin/python3` (system Python). Zabbix runs external scripts via the shebang directly — it does **not** activate venvs. After copying the script to `externalscripts/`, update the shebang to the venv Python:
>
> ```bash
> sed -i '1s|.*|#!/opt/zabbix-dns-monitoring/.venv/bin/python3|' /usr/lib/zabbix/externalscripts/mail.dns.audit
> ```
>
> Or use **Method B** (`python3-dnspython` via apt) — simpler and works without shebang changes.

Manual test:

```bash
/opt/zabbix-dns-monitoring/.venv/bin/python3 /usr/lib/zabbix/externalscripts/mail.dns.audit example.com
```

**Method B: System package (recommended for Zabbix)**

```bash
apt update
apt install -y python3-dnspython
```

If the `python3-dnspython` package is not found in the repository, use Method A.

**Method C: For migrating existing code (not recommended)**

If absolutely necessary to break the protection (at your own risk):

```bash
pip3 install dnspython --break-system-packages
```

This may break system dependencies when Python is updated.

#### Ubuntu/Debian (older versions before 22.04)

```bash
apt update
apt install -y python3 python3-pip
pip3 install dnspython
```

#### CentOS/RHEL

```bash
yum install -y python3 python3-pip
pip3 install dnspython
```

#### Alpine (container)

```bash
apk add --no-cache python3 py3-dnspython
```

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

# Test functionality
/usr/lib/zabbix/externalscripts/mail.dns.audit example.com 8.8.8.8 3
```

> **Zabbix Proxy:** If hosts are monitored by a **Zabbix Proxy**, deploy the script and Python dependencies on the **proxy server** — not the Zabbix Server. External check items run on whichever machine (server or proxy) monitors the host. The same installation steps apply to each proxy.

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
| `{$DNS_TIMEOUT_SEC}` | `3` | DNS query timeout (seconds) |
| `{$DNS_SHUFFLE}` | `1` | Shuffle resolvers (1/0) |
| `{$DNS_SLOW_MS}` | `3000` | Slow DNS threshold (ms) |

### SPF and Checks

| Macro | Value | Description |
|-------|-------|-------------|
| `{$SPF_MAX_LOOKUPS}` | `10` | Maximum lookups for SPF |
| `{$SPF_EXPECT_ALL}` | `-all\|~all` | Regex for "all" mechanism |
| `{$CIDR_ALLOWLIST}` | (empty) | Allowed CIDR for SPF |

### DNSBL Parameters

| Macro | Value | Description |
|-------|-------|-------------|
| `{$DNSBL_ZONES}` | `zen.spamhaus.org,bl.spamcop.net` | Zones to check |
| `{$DNSBL_CACHE_TTL_SEC}` | `1200` | DNSBL cache TTL (seconds) |
| `{$DNSBL_MAX_IP}` | `1` | Max IPs for DNSBL |
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
| `{$TEMPLATE_VERSION}` | `0.1.44` | Template version |
| `{$MAIL_DNS_NODATA_SEC}` | `1800` | nodata threshold (seconds) for master item |

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

### Built-in Simulations

```bash
# Simulate bad SPF
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0 \
  "zen.spamhaus.org" "" "10" "-all|~all" "1200" "5" "1" "default" "1" \
  --simulate bad_spf

# Simulate DNSBL
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0 \
  "zen.spamhaus.org" "" "10" "-all|~all" "1200" "5" "1" "default" "1" \
  --simulate dnsbl
```

### DNSBL Self-Test

```bash
# Check test IP status in DNSBL
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0 \
  "zen.spamhaus.org,bl.spamcop.net" "" "10" "-all|~all" "1200" "5" "1" "default" "1" \
  --dnsbl-test-ip 127.0.0.2
```

### Debug

```bash
# Enable debug output
DEBUG_DNSBL=1 ./externalscripts/mail.dns.audit example.com
```

## Troubleshooting

### Error: `error: externally-managed-environment` when installing dnspython

This is a PEP 668 error in Debian 12+ and Ubuntu 23.10+, which protects the system Python.

**Solution: use virtual environment**

```bash
apt install -y python3-full python3-venv

# Create environment
python3 -m venv /opt/dns-venv
. /opt/dns-venv/bin/activate

# Install package
pip install dnspython
```

Update the shebang in the deployed script to point to the venv Python:

```bash
sed -i '1s|.*|#!/opt/dns-venv/bin/python3|' /usr/lib/zabbix/externalscripts/mail.dns.audit
```

Or verify manually:

```bash
/opt/dns-venv/bin/python3 /usr/lib/zabbix/externalscripts/mail.dns.audit example.com
```

**Alternative: system package (if available)**

```bash
apt install -y python3-dnspython
```

### Python 3 Not Found

```bash
# Install Python on Zabbix server
apt install -y python3 python3-pip
pip3 install dnspython
```

### dnspython Not Installed

```bash
pip3 install dnspython>=2.0

# Or in container:
docker exec zabbix-server apk add --no-cache py3-dnspython
```

### DNSBL: "POLICY/ERROR" Status

Public resolvers (8.8.8.8) are blocked by DNSBL providers. Solution:

1. Install local resolver (Unbound/Bind) on local machine
2. Set macro: `{$DNS_RESOLVER} = "127.0.0.1"`

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

Full history: [CHANGELOG.md](CHANGELOG.md)

Recent updates:
- **v0.1.44** — DKIM: `rsa-unknown` instead of `rsa-0`; `dmarc_before`/`dmarc_after` tags on policy downgrade trigger
- **v0.1.43** — DKIM/DMARC change triggers now show before→after values in operational data
- **v0.1.42** — MX/SPF change triggers now show before→after values in operational data
- **0.1.41**: Trigger names improved: "DNS audit script error" now shows error text via `{ITEM.LASTVALUE}`; "DMARC rua= malformed" shows actual bad value; "DNS query slow" shows actual ms; fixed `{ITEM.LASTVALUE3}` bug in "MX IP listed in DNSBL" description (was resolving to nothing)
- **0.1.40**: "DNSBL check failed" trigger now shows the affected IP, zone, and failure reason inline in the problem name via `{?last(...mail.dnsbl.listed.details)}`; description updated with common causes and remediation (public resolver blocked, local Unbound recommended)
- **0.1.39**: DKIM key size: RSA min_key_bits and weak_key_count items; WARNING trigger (<2048 bits, suppressed when HIGH active) and HIGH trigger (≤1024 bits); DMARC adkim/aspf informational items; MX→CNAME RFC 5321 §5 violation WARNING trigger
- **0.1.38**: DMARC rua= checks split: opt-in absent alert (INFO, {$CHECK_DMARC_RUA}=0 by default) + always-on malformed alert (WARNING)
- **0.1.37**: Removed DMARC rua= missing trigger — rua= is optional per RFC 7489; absence is valid
- **0.1.36**: Bugfix — DNSBL trigger names now show exact response text; 6 missing skip macros added; 15 triggers restored error dependency; {$TEMPLATE_VERSION} corrected
- **0.1.35**: Macros to skip DNSSEC/MTA-STS/TLS-RPT/BIMI checks per host ({$CHECK_DNSSEC}, {$CHECK_MTA_STS}, {$CHECK_TLS_RPT}, {$CHECK_BIMI})
- **0.1.34**: Bugfix — DMARC rua= null handling, SPF a:hostname mx_covered detection, script VERSION sync
- **0.1.33**: 8 new triggers (MX missing, SPF RFC violations, hash change detection, DMARC rua, DNSBL failures), error dependencies on all triggers, NS trigger fix, {$MAIL_CLIENT_AUTOCONFIG_CHECK} macro
- **v0.1.32** (2026-02-20): Added `mail.script.version` item and WARNING trigger for version mismatch against `{$TEMPLATE_VERSION}` — detects outdated script on proxies.
- **v0.1.31** (2026-02-20): Fixed script shebang (`#!/usr/bin/python3`); added `.gitattributes` for LF line endings — fixes script execution failure in Zabbix caused by CRLF and missing PATH.
- **v0.1.30** (2026-02-20): Raised DMARC p=none trigger severity to WARNING; added HIGH trigger for DMARC policy downgrade (quarantine/reject → none).
- **v0.1.29** (2026-02-20): Added mail client autoconfiguration DNS checks (autoconfig, autodiscover, SRV) with corresponding triggers.
- **v0.1.28** (2026-02-20): Improved trigger informativeness — added {HOST.HOST}, contextual data, and descriptions with remediation guidance.
- **v0.1.27** (2026-01-13): Replaced {HOST.NAME} with {HOST.HOST} in item keys for reliability.
- **v0.1.26** (2025-12-30): Fixed timeout issues — {$DNS_RESOLVER} is now empty by default to use the system resolver.
- **v0.1.18** (2025-12-26): Added nodata trigger for the master item (detecting timeouts/no data).
- **v0.1.17** (2025-12-26): Added duplicate DNS checks/triggers (MX, DMARC, DKIM, NS, SOA).
- **v0.1.16** (2025-12-24): Removed UUIDs from template for portability.

## Links

- GitHub: https://github.com/IT-for-Prof/zabbix-mail-dns-audit
- Website: https://itforprof.com
- Issues: https://github.com/IT-for-Prof/zabbix-mail-dns-audit/issues

