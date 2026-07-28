import requests

VCO_URL = "https://vco.internal.example.com"

def api_call(token, method, endpoint, payload=None):
    resp = requests.request(
        method, f"{VCO_URL}/portal/rest/{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    resp.raise_for_status()
    return resp.json()

def create_edge_profile(token, site):
    payload = {
        "name": f"{site['site_id']}-profile",
        "enterpriseId": site["enterprise_id"],
        "configurationId": site["base_config_id"],
    }
    return api_call(token, "POST", "edge/insertEdge", payload)

def activate_ztp(token, edge_id, serial_number):
    payload = {"edgeId": edge_id, "serialNumber": serial_number, "activationState": "PENDING"}
    return api_call(token, "POST", "edge/activateEdge", payload)

if __name__ == "__main__":
    token = "<use env var, not hardcoded>"
    site = {"site_id": "branch-042", "enterprise_id": 1001, "base_config_id": 55}
    edge = create_edge_profile(token, site)
    activate_ztp(token, edge["id"], serial_number="VC2100-88213")
    print(f"Edge {edge['id']} activated for zero-touch provisioning")
