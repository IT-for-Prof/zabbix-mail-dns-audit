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
- ✅ DKIM key tracking
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

## Requirements

- Zabbix 7.0+
- Python 3.6+
- dnspython 2.0+
- Linux/Unix environment
- Internet access for DNS and DNSBL queries

## Quick Start

### Step 1: Install Dependencies

**Ubuntu/Debian:**
```bash
apt update
apt install -y python3 python3-pip
pip3 install dnspython
```

**CentOS/RHEL:**
```bash
yum install -y python3 python3-pip
pip3 install dnspython
```

**Alpine (container):**
```bash
apk add --no-cache python3 py3-pip
pip3 install dnspython
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
   - Interfaces: Zabbix server IP (localhost)
4. Go to Templates tab
5. Add `Template Mail DNS Audit Zabbix`
6. Create

## Configuration

All parameters are configured via template macros in Zabbix:

### Network Parameters

| Macro | Value | Description |
|-------|-------|-------------|
| `{$DNS_RESOLVER}` | `127.0.0.1,9.9.9.10,...` | Resolver IPs (comma-separated). Empty = system |
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

### Other

| Macro | Value | Description |
|-------|-------|-------------|
| `{$CHECK_IPV6}` | `0` | Check AAAA records (1/0) |
| `{$DKIM_SELECTORS}` | `default` | DKIM selectors |
| `{$TEMPLATE_VERSION}` | `0.1.25` | Template version |
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
Zabbix Server
    ↓
mail.dns.audit (Master Item)
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

- DNSBL results stored in `/tmp/mail_dns_audit_cache.json`
- TTL managed by macro `{$DNSBL_CACHE_TTL_SEC}` (default 1200 sec)
- Cache speeds up repeated checks and reduces load

## Changelog

Full history: [CHANGELOG.md](CHANGELOG.md)

Recent updates:
- **v0.1.18** (2025-12-26): Added nodata trigger for the master item (detecting timeouts/no data).
- **v0.1.17** (2025-12-26): Added duplicate DNS checks/triggers (MX, DMARC, DKIM, NS, SOA).
- **v0.1.16** (2025-12-24): Removed UUIDs from template for portability.
- **v0.1.15** (2025-12-24): Added resolver shuffle control via `{$DNS_SHUFFLE}` macro
- **v0.1.13** (2025-12-24): DNSBL fallback via alternate resolvers
- **v0.1.10** (2025-12-24): GitHub repository link in description

## License

MIT License © itforprof.com by Konstantin Tyutyunnik

## Links

- GitHub: https://github.com/IT-for-Prof/zabbix-mail-dns-audit
- Website: https://itforprof.com
- Issues: https://github.com/IT-for-Prof/zabbix-mail-dns-audit/issues

