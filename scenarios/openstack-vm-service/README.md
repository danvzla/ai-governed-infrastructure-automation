# OpenStack VM & Service Provisioning

`Heat · OpenStack SDK · Ansible`

A Heat template defines the VM, its ports, and its security group as one declarative stack rather than a sequence of separate Nova/Neutron/Horizon steps, the Python SDK client deploys the stack as a single atomic operation, and Ansible only takes over afterward for in-guest service configuration Heat isn’t well suited for.

## Problem

Provisioning a new NFV workload's VM instance and its supporting network services (floating IP, security groups) on the OpenStack telco cloud is done through a sequence of manual Horizon dashboard steps and CLI commands run in a specific, undocumented order. Newer team members regularly provision instances with missing security group rules or unassigned floating IPs, requiring rework.

## Methodology

Replaced the manual Horizon/CLI sequence with a Heat Orchestration Template defining the VM, its network ports, and its security group as a single declarative stack, deployed through the OpenStack SDK as one atomic operation, with Ansible layered on top only for post-boot, in-guest service configuration that Heat itself isn't well suited for.

## Architecture

A Heat template defines the VM, its ports, and its security group as one declarative stack rather than a sequence of separate Nova/Neutron/Horizon steps, the Python SDK client deploys the stack as a single atomic operation, and Ansible only takes over afterward for in-guest service configuration Heat isn’t well suited for.

## Design decisions

**ADR-01: Define the VM, network ports, and security group as a single Heat stack rather than sequential Nova/Neutron API calls**

- Why: The original manual process’s failures (missing security group rules, unassigned floating IPs) all came from steps being run separately and sometimes skipped, a single declarative stack can’t be partially applied the way a manual sequence can be partially forgotten.
- Trade-off accepted: Heat’s declarative model is less flexible mid-deployment than direct API calls; a stack update sometimes needs care to avoid unwanted resource replacement.

**ADR-02: Use Ansible only for post-boot, in-guest configuration, not for the OpenStack resource provisioning itself**

- Why: Heat is the right tool for OpenStack resource lifecycle, it understands rollback and dependency ordering natively. Ansible is the right tool for what happens inside the VM after it boots.
- Trade-off accepted: Two tools in the pipeline instead of one, requiring the handoff between them (stack output → Ansible dynamic inventory) to stay reliable.

**ADR-03: Default every new VM’s security group to deny-by-default with an explicit allow list generated from the template**

- Why: With the process manual and undocumented, security group rules were the step most often skipped by newer team members. Making it part of the atomic stack removes the "forgot to add it" failure mode entirely.
- Trade-off accepted: A genuinely novel access requirement needs a template update and redeploy, rather than a quick manual rule addition.

## What we chose not to automate, and why

Assignment of a VM to a specific compute host or availability zone for anti-affinity or capacity reasons remains a manual decision by the infrastructure lead for latency-sensitive NFV workloads, the scheduler’s default placement logic is trusted for standard workloads but not overridden automatically for these higher-sensitivity cases.

## AI remediation agent

- **Trigger:** Post-boot service health check fails: the service on nfv-workload-purple-01 is not listening on the expected port after a 30-second timeout.
- **Reasoning:** The agent checks whether this failure matches a known transient pattern, package manager lock contention during boot, which historically accounts for roughly 70% of these failures, versus a genuine configuration error.
- **Decision:** Conditional, one automatic retry, escalate if it recurs
- **Action:** Triggers a single automatic re-run of the Ansible post-boot play with a backoff delay; if the service comes up, the case is logged as a transient retry and closed.
- **Escalation boundary:** A second consecutive failure is treated as a real configuration problem, not a transient one, the agent halts further auto-retries and escalates with the collected logs attached, rather than retrying indefinitely and masking a genuine issue.

See `../../shared/remediation_agent.py` for the shared orchestration engine.

## Repository structure

```
.
├── .github/
│   └── workflows/
│       └── vm-provision.yml
├── policy/
│   └── guardrails.rego
├── scripts/
│   ├── remediation-agent.sh
│   └── validate-service-health.sh
├── README.md
├── configure_services.yml
├── deploy_stack.py
└── vm_stack.yaml
```

## Getting started

1. Review `deploy_stack.py` and set required environment variables (API tokens, credentials).
2. Run the pre-flight / validation script: `python deploy_stack.py`
3. Apply configuration: `ansible-playbook configure_services.yml`
4. Reference pipeline: `.github/workflows/vm-provision.yml` (illustrative, not wired to live infrastructure)

## Disclaimer

Illustrative demo content using non-client, non-production data, created solely to demonstrate capability. Figures, timings, and outcomes are examples, not client results.
