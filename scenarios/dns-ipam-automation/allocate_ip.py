import pynetbox

NETBOX_URL = "https://netbox.internal.example.com"

def allocate_ip(token, prefix, hostname, site):
    nb = pynetbox.api(NETBOX_URL, token=token)

    prefix_obj = nb.ipam.prefixes.get(prefix=prefix, site=site)
    if prefix_obj is None:
        raise ValueError(f"No matching prefix found for site {site}")

    available = prefix_obj.available_ips.list()
    if not available:
        raise RuntimeError(f"Prefix {prefix} has no available addresses")

    ip = available[0]
    reserved = nb.ipam.ip_addresses.create(
        address=ip.address,
        status="reserved",
        dns_name=f"{hostname}.internal.example.com",
    )
    return reserved

if __name__ == "__main__":
    result = allocate_ip(
        token="<use env var, not hardcoded>",
        prefix="10.20.4.0/24",
        hostname="web-app-07",
        site="dal-dc1",
    )
    print(f"Reserved {result.address} for {result.dns_name}")
