# Multi-Cloud VPC Provisioning

`AWS · GCP · Azure`

Picture one shared ledger of address blocks, not three separate ones per cloud.

## Problem

Application teams request a new VPC network in whichever cloud their workload runs, AWS, GCP, or Azure, but provisioning is done by a different engineer with a different manual process for each cloud. CIDR ranges have been assigned independently per cloud, and two teams already hit an IP overlap when trying to connect an AWS VPC to a GCP VPC over Cloud Interconnect.

## Methodology

Built one intake request, team, environment, target cloud, that allocates a non-overlapping CIDR block from a single address pool shared across all three clouds, then routes to the matching Ansible cloud collection (amazon.aws, google.cloud, or azure.azcollection) to provision that cloud's native VPC/VNet, subnets, and routing. The same shared pool prevents the overlap problem regardless of which cloud a team picks.

## Architecture

Picture one shared ledger of address blocks, not three separate ones per cloud. Every VPC request, AWS, GCP, or Azure alike, checks the same ledger and takes the next unused block: request 1 gets 10.0.0.0/24, request 2 gets 10.0.1.0/24, request 3 gets 10.0.2.0/24, regardless of which cloud each one targets. Because every cloud draws from that same list, two clouds can never end up holding the same range. A cloud router then hands the request to the matching Ansible collection, which provisions that cloud's native VPC/VNet using its own naming and resource model.

## Design decisions

**ADR-01: Draw CIDR allocations for all three clouds from one shared address pool, rather than letting each cloud team manage its own range independently**

- Why: The incident that triggered this project was an IP overlap discovered only when two teams tried to connect an AWS VPC to a GCP VPC, independent per-cloud allocation can’t prevent that by design, no matter how careful either team is individually.
- Trade-off accepted: Every cloud’s provisioning now depends on one shared allocator being available and correct, rather than being fully independent.

**ADR-02: Use each cloud’s own Ansible collection rather than building one abstraction that hides all three behind a single interface**

- Why: AWS, GCP, and Azure model networking differently enough (VPC/Subnet/Route Table vs. VPC Network/Subnetwork vs. VNet/Subnet) that forcing one shared abstraction would either hide capability or become its own maintenance burden.
- Trade-off accepted: Three collections to keep current instead of one, and anyone maintaining this needs baseline familiarity with all three clouds’ networking models.

**ADR-03: Keep cross-cloud connectivity (peering, interconnect, VPN between two clouds) as a manual review gate rather than self-service**

- Why: Connecting two clouds’ address space together has security and cost implications beyond either team’s own VPC, this is exactly the kind of decision that caused the original incident when it happened without coordinated review.
- Trade-off accepted: Adds a wait step to any workflow that genuinely needs cross-cloud connectivity.

## What we chose not to automate, and why

Requesting connectivity between two clouds, VPC peering, Cloud Interconnect, or a cross-cloud VPN, is never self-service. It always routes to manual review by a cloud network architect, since a connection between two clouds' address space carries security and cost implications beyond what either originating team can evaluate alone.

## AI remediation agent

- **Trigger:** An Azure VNet provisioning run fails a tag-policy check: the new VNet is missing the required 'cost-center' tag, the same check applies regardless of which cloud a request targets.
- **Reasoning:** The agent classifies this as a missing-metadata failure rather than an infrastructure failure, the resource configuration itself is valid, and no partial or inconsistent state was left behind by the failed run.
- **Decision:** Auto-remediate
- **Action:** Reads the cost-center value from the original intake request and re-runs only the tagging task for the Azure VNet, using the same azure.azcollection task the initial provisioning used, then re-validates the tag is present.
- **Escalation boundary:** If the intake request itself never captured a cost-center value, the agent can’t infer one for any cloud and escalates to the requester rather than guessing, this check and this escalation boundary are identical whether the request targeted AWS, GCP, or Azure.

See `../../shared/remediation_agent.py` for the shared orchestration engine.

## Repository structure

```
.
├── .github/
│   └── workflows/
│       └── vpc-provision.yml
├── scripts/
│   ├── apply-cost-tags.sh
│   └── remediation-agent.sh
├── README.md
├── allocate_cidr.py
└── provision_vpc.yml
```

## Getting started

1. Review `allocate_cidr.py` and set required environment variables (API tokens, credentials).
2. Run the pre-flight / validation script: `python allocate_cidr.py`
3. Apply configuration: `ansible-playbook provision_vpc.yml`
4. Reference pipeline: `.github/workflows/vpc-provision.yml` (illustrative, not wired to live infrastructure)

## Disclaimer

Illustrative demo content using non-client, non-production data, created solely to demonstrate capability. Figures, timings, and outcomes are examples, not client results.
