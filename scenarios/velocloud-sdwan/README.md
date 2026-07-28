# VeloCloud SD-WAN: Branch Onboarding

`VeloCloud Orchestrator · Python`

New sites are never configured directly in the Orchestrator UI, a Python client creates the Edge profile and triggers Zero Touch Provisioning from inventory data, and Ansible applies the standardized Business Policy and segment baseline at the Profile level, so policy stays consistent across every site regardless of which engineer onboarded it.

## Problem

New branch sites are onboarded to the SD-WAN fabric by hand in VeloCloud Orchestrator, an engineer manually creates the Edge profile, Business Policy rules, and segments for each site, taking roughly half a day per site and producing inconsistent QoS and policy configuration depending on which engineer did the onboarding.

## Methodology

Standardized branch onboarding around VeloCloud's own Zero Touch Provisioning model: a Python client using the SD-WAN Orchestrator API creates the Edge profile and triggers activation from a site inventory, then Ansible applies a standardized Business Policy and segment baseline at the Profile level, so every site inherits the same policy instead of an engineer re-creating it by hand each time.

## Architecture

New sites are never configured directly in the Orchestrator UI, a Python client creates the Edge profile and triggers Zero Touch Provisioning from inventory data, and Ansible applies the standardized Business Policy and segment baseline at the Profile level, so policy stays consistent across every site regardless of which engineer onboarded it.

## Design decisions

**ADR-01: Apply Business Policy at the Profile level as default, allowing Edge-level overrides only by exception**

- Why: The original inconsistency came from engineers configuring policy per-Edge from scratch; a shared Profile baseline is the only way to guarantee new sites start from the same policy set.
- Trade-off accepted: Sites with genuinely unique requirements need an explicit override step rather than free-form configuration, a small process overhead for legitimate edge cases.

**ADR-02: Use Zero Touch Provisioning rather than manually associating each Edge to its profile in the Orchestrator UI**

- Why: ZTP is the mechanism VeloCloud’s own architecture is built around for low-touch deployment, the manual UI path was recreating work the platform already automates.
- Trade-off accepted: Requires accurate serial-number/site inventory data upfront, or an Edge activates against the wrong profile.

**ADR-03: Keep DMPO (Dynamic Multipath Optimization) enabled by default on all WAN links rather than opt-in per site**

- Why: DMPO is the core value proposition of the SD-WAN overlay; leaving it opt-in was the single most common misconfiguration found in the audit that triggered this project.
- Trade-off accepted: Sites with a single WAN link gain no benefit from DMPO but still carry its default-on configuration overhead.

## What we chose not to automate, and why

Segment-level firewall exceptions requested by a specific business unit still require manual security-team review before being added to the Business Policy baseline, segmentation changes touch every site inheriting that Profile, so this stays a deliberate governance checkpoint rather than a self-service change.

## AI remediation agent

- **Trigger:** Post-push verification detects DMPO disabled on the WAN link at branch-042 (expected: enabled).
- **Reasoning:** The agent checks the failure against a library of known drift patterns rather than treating it as novel: DMPO state is a single boolean toggle with no downstream dependency risk, and this exact pattern has occurred 40+ times before with a clean auto-fix outcome each time.
- **Decision:** Auto-remediate
- **Action:** Re-applies DMPO=enabled via the Orchestrator API, re-verifies the change took effect, and logs the correction to the site's change record for audit.
- **Escalation boundary:** If the same link fails DMPO verification twice within 24 hours, auto-fix is disabled for that link and the case is escalated to a network engineer instead, a repeat failure suggests a hardware or link-layer issue that an API retry can't actually fix, and continuing to auto-correct it would mask the real problem.

See `../../shared/remediation_agent.py` for the shared orchestration engine.

## Repository structure

```
.
├── .github/
│   └── workflows/
│       └── branch-onboarding.yml
├── inventory/
│   └── site_inventory.csv
├── policy/
│   └── guardrails.rego
├── scripts/
│   ├── remediation-agent.sh
│   └── verify-site-policy.sh
├── README.md
├── apply_business_policy.yml
├── baseline_business_policy.json
├── baseline_segments.json
└── velocloud_provision.py
```

## Getting started

1. Review `velocloud_provision.py` and set required environment variables (API tokens, credentials).
2. Run the pre-flight / validation script: `python velocloud_provision.py`
3. Apply configuration: `ansible-playbook apply_business_policy.yml`
4. Reference pipeline: `.github/workflows/branch-onboarding.yml` (illustrative, not wired to live infrastructure)

## Disclaimer

Illustrative demo content using non-client, non-production data, created solely to demonstrate capability. Figures, timings, and outcomes are examples, not client results.
