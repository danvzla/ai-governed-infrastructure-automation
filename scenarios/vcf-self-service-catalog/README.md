# VCF Self-Service Catalog

`VCF Automation · Blueprints`

A team never builds their own environment or files a ticket for a standard need, they pick a pre-approved Blueprint from the catalog, set a few variables, and the VCF Automation API provisions it with policy, quota, and cost tags already attached, while a separate governance layer tracks consumption per team continuously rather than at request time only.

## Problem

Application teams that just need a standard VM environment or a small Kubernetes cluster still have to file a ticket and wait for a platform engineer to hand-build it, even though VCF Automation ships a self-service catalog specifically designed to let teams request pre-approved environments themselves. The catalog capability exists, but nothing has been published to it, so every request still goes through the manual queue.

## Methodology

Published a small, curated set of pre-approved Blueprints to the VCF Automation Self-Service Catalog, a standard 3-tier VM environment, a small VKS (Kubernetes) cluster, and a database stack, so application teams request directly from a catalog, the way they'd use an internal app store, instead of filing a ticket. Every blueprint carries its policy, quota, and cost tags automatically, so what gets provisioned is compliant by construction rather than checked after the fact.

## Architecture

A team never builds their own environment or files a ticket for a standard need, they pick a pre-approved Blueprint from the catalog, set a few variables, and the VCF Automation API provisions it with policy, quota, and cost tags already attached, while a separate governance layer tracks consumption per team continuously rather than at request time only.

## Design decisions

**ADR-01: Publish a small, curated set of blueprints rather than trying to cover every possible request type**

- Why: A catalog with too many options recreates the complexity it was meant to remove, three well-chosen blueprints covering most real requests are more trustworthy than twenty half-configured ones.
- Trade-off accepted: Requests outside the curated set still need the manual/ticket path, this shrinks that path, it doesn’t eliminate it.

**ADR-02: Attach policy and cost tags at the blueprint level, not as a separate step after provisioning**

- Why: A separate "add tags after" step is exactly the kind of easy-to-skip step that caused inconsistency elsewhere in this portfolio, building it into the blueprint makes it structurally impossible to provision without it.
- Trade-off accepted: Changing a policy later means updating and republishing the blueprint definition, not just patching one resource.

**ADR-03: Enforce quota at request time (blocking the request) rather than after provisioning (needing cleanup)**

- Why: It is far cheaper to tell a team they’re over quota before anything is built than to build it and walk it back afterward.
- Trade-off accepted: A team with a genuine one-time need for an exception has to go through a manual quota-increase request rather than provisioning first and asking forgiveness later.

## What we chose not to automate, and why

Requests for resources outside the published blueprint catalog, a nonstandard VM size, an unsupported OS, a custom network topology, still route to the manual engineering queue. The catalog is intentionally narrow; broadening it happens deliberately by adding new reviewed blueprints, not through ad hoc exceptions.

## AI remediation agent

- **Trigger:** The Small VKS Cluster blueprint starts failing at the storage-provisioning step for roughly 15% of new requests, shortly after a platform storage backend change.
- **Reasoning:** The agent correlates failures across recent requests rather than evaluating each one independently, and notices multiple unrelated teams hitting the identical failure at the identical step, that pattern points to the platform itself, not to anything the requesters did differently.
- **Decision:** Escalate
- **Action:** Pauses the affected blueprint in the catalog (marks it temporarily unavailable to new requests) and opens a high-priority case to the platform team with the correlated failure pattern attached.
- **Escalation boundary:** This is escalate-by-default: the agent does not attempt to auto-fix a platform-level storage issue itself. The blast radius, every team using this blueprint, and the ambiguity of the root cause both exceed its auto-fix threshold, so pausing the catalog item and notifying humans is the safest immediate action available to it.

See `../../shared/remediation_agent.py` for the shared orchestration engine.

## Repository structure

```
.
├── .github/
│   └── workflows/
│       └── publish-blueprint.yml
├── blueprints/
│   ├── database-stack.yaml
│   ├── small-vks-cluster.yaml
│   └── standard-vm.yaml
├── policy/
│   └── guardrails.rego
├── scripts/
│   └── remediation-agent.sh
├── README.md
├── configure_catalog_access.yml
└── publish_blueprint.py
```

## Getting started

1. Review `publish_blueprint.py` and set required environment variables (API tokens, credentials).
2. Run the pre-flight / validation script: `python publish_blueprint.py`
3. Apply configuration: `ansible-playbook configure_catalog_access.yml`
4. Reference pipeline: `.github/workflows/publish-blueprint.yml` (illustrative, not wired to live infrastructure)

## Disclaimer

Illustrative demo content using non-client, non-production data, created solely to demonstrate capability. Figures, timings, and outcomes are examples, not client results.
