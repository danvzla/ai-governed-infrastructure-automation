import json
import ipaddress

POOL_FILE = "cidr_pool_state.json"
PARENT_BLOCK = ipaddress.ip_network("10.0.0.0/12")  # ~1M addresses, cut into /24 blocks
SUBNET_SIZE = 24

# One shared ledger, not one per cloud. Every request - AWS, GCP, or Azure -
# reads the SAME pool_state file and takes the next unused /24:
#   request 1 (AWS)   -> 10.0.0.0/24
#   request 2 (GCP)   -> 10.0.1.0/24
#   request 3 (Azure) -> 10.0.2.0/24
# Because all three clouds draw from this one list, two clouds can never be
# handed the same range - there is no second list to accidentally duplicate from.

def load_state():
    try:
        with open(POOL_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"allocated": []}

def save_state(state):
    with open(POOL_FILE, "w") as f:
        json.dump(state, f, indent=2)

def allocate_cidr(owner, environment, cloud):
    state = load_state()
    allocated = {ipaddress.ip_network(c) for c in state["allocated"]}
    for candidate in PARENT_BLOCK.subnets(new_prefix=SUBNET_SIZE):
        if candidate not in allocated:
            state["allocated"].append(str(candidate))
            save_state(state)
            return {"cidr": str(candidate), "owner": owner, "environment": environment, "cloud": cloud}
    raise RuntimeError("Shared CIDR pool exhausted")

def route_to_cloud(cloud):
    routing = {"aws": "amazon.aws", "gcp": "google.cloud", "azure": "azure.azcollection"}
    if cloud not in routing:
        raise ValueError(f"Unknown target cloud: {cloud}")
    return routing[cloud]

if __name__ == "__main__":
    result = allocate_cidr(owner="team-checkout", environment="staging", cloud="gcp")
    collection = route_to_cloud(result["cloud"])
    print(f"Allocated {result['cidr']} on {result['cloud']}, provisioning via {collection}")
