# DNS & IPAM Automation

`NetBox · Python · Ansible`

An IP address is never chosen by hand from a spreadsheet, NetBox holds the authoritative record of every prefix and allocation, a Python client using pynetbox reserves the next available address directly from NetBox, and Ansible creates the matching DNS record immediately afterward, so the two are never out of sync.

## Problem

New servers and network devices get their IP addresses assigned by an engineer manually checking a shared spreadsheet for the next free address, then hand-editing a DNS zone file. This has produced duplicate IP assignments twice in the last year, and DNS records that silently go stale when a server is decommissioned but its record is never removed.

## Methodology

Adopted NetBox as the single source of truth for IP address space and DNS naming, replacing the spreadsheet entirely. A Python client using the pynetbox library allocates the next available IP from the correct NetBox prefix and reserves it before anything is provisioned, and an Ansible playbook creates the matching DNS record, so an IP is never assigned without NetBox recording it, and a DNS record is never created without a NetBox-registered IP behind it.

## Architecture

An IP address is never chosen by hand from a spreadsheet, NetBox holds the authoritative record of every prefix and allocation, a Python client using pynetbox reserves the next available address directly from NetBox, and Ansible creates the matching DNS record immediately afterward, so the two are never out of sync. A decommission hook reverses both steps together when a host is retired, which is the step the spreadsheet process never reliably did.

## Design decisions

**ADR-01: Make NetBox the single source of truth for both IP allocation and DNS naming, rather than keeping IPAM data and DNS zone files as two separately maintained records**

- Why: The duplicate-IP incidents happened because the spreadsheet and the DNS zone file could each be edited independently and drift apart, one source of truth removes the possibility of the two disagreeing.
- Trade-off accepted: Every DNS change now has to go through NetBox first, even a small one, rather than a quick direct zone-file edit.

**ADR-02: Reserve the IP in NetBox before creating the DNS record, rather than creating the DNS record first**

- Why: An IP address collision is a worse failure than a DNS record briefly not existing yet, reserving first guarantees the address is safe to use before anything else depends on it.
- Trade-off accepted: A failure between the reservation and the DNS step leaves a reserved-but-unused IP, which needs periodic cleanup rather than never happening.

**ADR-03: Bind decommissioning to release the IP and remove the DNS record in one step, rather than two separately triggered cleanup tasks**

- Why: The stale-DNS-record problem was specifically caused by decommissioning being a two-step manual process where the second step (removing DNS) was routinely forgotten, combining them removes that failure mode entirely.
- Trade-off accepted: A team that wants to keep a DNS record alive temporarily after decommissioning (e.g., during a migration) needs an explicit override, since the default now always removes both together.

## What we chose not to automate, and why

Reassigning a previously-decommissioned IP address to a new host before its DNS cache/TTL cooldown has elapsed still requires manual override approval, reusing an address too soon risks a stale DNS cache somewhere on the network resolving the old hostname to the new host's traffic, and that's judged worth a deliberate human check rather than a timer nobody trusts.

## AI remediation agent

- **Trigger:** NetBox's change log shows a device deleted, but the corresponding DNS record was not removed within the expected decommission window.
- **Reasoning:** The agent checks whether this is a genuine missed step versus an intentional exception, it looks for an active 'DNS retained' override tag on the record before assuming this is a failure that needs correcting.
- **Decision:** Auto-remediate
- **Action:** Removes the orphaned DNS record and releases the associated IP address back to the available pool in NetBox, logging the cleanup action against the original decommission ticket.
- **Escalation boundary:** If an override tag is present, the agent takes no action and simply logs that the retained record was checked and intentionally skipped, it never removes a record a human deliberately chose to keep, regardless of how long it's been retained.

See `../../shared/remediation_agent.py` for the shared orchestration engine.

## Repository structure

```
.
├── .github/
│   └── workflows/
│       └── ipam-provision.yml
├── policy/
│   └── guardrails.rego
├── scripts/
│   ├── remediation-agent.sh
│   └── verify-dns-resolution.sh
├── README.md
├── allocate_ip.py
└── create_dns_record.yml
```

## Getting started

1. Review `allocate_ip.py` and set required environment variables (API tokens, credentials).
2. Run the pre-flight / validation script: `python allocate_ip.py`
3. Apply configuration: `ansible-playbook create_dns_record.yml`
4. Reference pipeline: `.github/workflows/ipam-provision.yml` (illustrative, not wired to live infrastructure)

## Disclaimer

Illustrative demo content using non-client, non-production data, created solely to demonstrate capability. Figures, timings, and outcomes are examples, not client results.
