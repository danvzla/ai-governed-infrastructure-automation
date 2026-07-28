# Network Config Backup & Compliance

`NAPALM · NETCONF · gNMI`

One Python script using NAPALM connects to both Cisco and Juniper devices through the same interface for nightly backup and compliance scanning.

## Problem

Configuration backups for Cisco and Juniper network devices are pulled manually and inconsistently, some engineers save a running-config snapshot before a change, most don't, and there's no standing way to know whether a device's configuration has drifted from its approved baseline until something breaks and someone finally goes looking.

## Methodology

Adopted NAPALM as a single, vendor-neutral Python interface to both Cisco and Juniper devices for nightly backup and compliance scanning, replacing separate per-vendor scripts. gNMI streaming telemetry adds a second, real-time detection path that catches security-sensitive drift within seconds instead of waiting for the next nightly run. For drift categories the compliance policy marks auto-fixable, a NETCONF client (ncclient) pushes a Jinja2-rendered corrective payload through NETCONF's candidate/commit/rollback model, a safer mechanism for automated changes than a plain SSH config merge.

## Architecture

One Python script using NAPALM connects to both Cisco and Juniper devices through the same interface for nightly backup and compliance scanning. gNMI streaming telemetry runs alongside it as a faster, real-time detection path for security-sensitive changes. When a flagged drift category is marked auto-fixable, a NETCONF client renders a Jinja2 payload and pushes it through NETCONF's candidate/commit/rollback model rather than a plain config merge, the same golden-config definition backs both the nightly and real-time paths.

## Design decisions

**ADR-01: Use NAPALM as one vendor-neutral interface rather than maintaining separate Cisco and Juniper backup scripts**

- Why: The two scripts that existed before this project had already drifted apart in what they captured and how they formatted output, making backups inconsistent between vendors even when both existed. One interface removes that as a source of inconsistency by construction.
- Trade-off accepted: The team is now dependent on NAPALM’s abstraction being accurate for both platforms, rather than having full direct control over each vendor’s native tooling.

**ADR-02: Store every nightly backup as a Git commit rather than overwriting a single "latest backup" file per device**

- Why: A Git history is itself the audit trail, the ability to see exactly when a specific line changed and compare any two points in time was a real gap the previous single-snapshot approach couldn’t answer.
- Trade-off accepted: The repository grows every night for every device, which needs periodic housekeeping that a single-snapshot file never required.

**ADR-03: Use NETCONF’s candidate/commit model for automated corrective pushes, rather than a plain SSH config merge**

- Why: NETCONF’s candidate datastore lets the corrective change be validated before it’s committed, and gives an explicit rollback point if the commit causes an unexpected problem, a plain SSH-pushed merge doesn’t have that safety net built in.
- Trade-off accepted: Only devices with NETCONF enabled can use the auto-fix path; devices without it fall back to detection-and-escalate only, even for otherwise low-risk drift categories.

## What we chose not to automate, and why

Applying a fix for a flagged compliance violation is not automatic by default, even with the NETCONF auto-fix path available, only drift categories explicitly marked auto-fixable in the compliance policy are eligible. Every other flagged device still requires a network engineer to review the specific change and decide whether to revert it, update the golden config to reflect an intentional change, or investigate further.

## AI remediation agent

- **Trigger:** gNMI streaming telemetry flags a Juniper edge router within seconds of the change occurring, the running config now includes an SNMP community string not present in the approved golden config, the same definition the nightly NAPALM job also checks.
- **Reasoning:** The agent checks whether the specific line that drifted matches a category of low-risk, cosmetic drift (like a description or comment field) or a category the compliance policy explicitly marks as security-sensitive, SNMP community strings are flagged as security-sensitive by definition, regardless of what the actual value is.
- **Decision:** Escalate
- **Action:** Does not attempt to revert the SNMP configuration automatically, even though the NETCONF auto-fix path exists and could technically apply the correction in seconds. Opens a case to the network security team with the specific diff, the device, and the exact detection timestamp from the gNMI stream.
- **Escalation boundary:** Any drift categorized as security-sensitive in the compliance policy escalates by default, regardless of how simple the actual fix would be or how fast the auto-fix path could apply it, the agent doesn’t evaluate whether a specific SNMP string change is dangerous or benign, because that judgment call belongs to a human reviewing the specific context, not a pattern-matched auto-fix.

See `../../shared/remediation_agent.py` for the shared orchestration engine.

## Repository structure

```
.
├── .github/
│   └── workflows/
│       └── network-compliance.yml
├── scripts/
│   └── remediation-agent.sh
├── README.md
├── backup_and_check.py
├── golden_config.yaml
└── nightly_backup.yml
```

## Getting started

1. Review `backup_and_check.py` and set required environment variables (API tokens, credentials).
2. Run the pre-flight / validation script: `python backup_and_check.py`
3. Apply configuration: `ansible-playbook nightly_backup.yml`
4. Reference pipeline: `.github/workflows/network-compliance.yml` (illustrative, not wired to live infrastructure)

## Disclaimer

Illustrative demo content using non-client, non-production data, created solely to demonstrate capability. Figures, timings, and outcomes are examples, not client results.
