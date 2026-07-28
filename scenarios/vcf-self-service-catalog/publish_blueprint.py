import requests
import yaml

VCF_AUTOMATION_URL = "https://vcf-automation.internal.example.com"

def validate_blueprint(spec):
    required = ["name", "policy_tags", "cost_center_required", "quota_class"]
    missing = [f for f in required if f not in spec]
    if missing:
        raise ValueError(f"Blueprint missing required fields: {missing}")
    return True

def publish_blueprint(token, spec_path):
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    validate_blueprint(spec)

    resp = requests.post(
        f"{VCF_AUTOMATION_URL}/automation/api/catalog/blueprints",
        headers={"Authorization": f"Bearer {token}"},
        json=spec
    )
    resp.raise_for_status()
    return resp.json()["id"]

if __name__ == "__main__":
    token = "<use env var, not hardcoded>"
    blueprint_id = publish_blueprint(token, "blueprints/small-vks-cluster.yaml")
    print(f"Published blueprint {blueprint_id} to self-service catalog")
