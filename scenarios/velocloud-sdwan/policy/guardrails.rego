package guardrails

# policy/guardrails.rego
# Supporting file referenced by this automation pipeline.
# Abbreviated placeholder for demo purposes, not full production content.

default allow = false

allow {
  input.policy_tags
  input.cost_center_required
}
