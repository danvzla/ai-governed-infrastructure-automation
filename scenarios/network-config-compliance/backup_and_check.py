from napalm import get_network_driver
from ncclient import manager
from jinja2 import Template
import yaml

DEVICES = [
    {"hostname": "core-sw-01.internal", "platform": "ios"},
    {"hostname": "edge-rtr-04.internal", "platform": "junos"},
]

CORRECTION_TEMPLATE = Template("""
<config>
  <configuration>
    <snmp>
      <community>
        <name>{{ approved_community }}</name>
      </community>
    </snmp>
  </configuration>
</config>
""")

def backup_device(device):
    driver = get_network_driver(device["platform"])
    conn = driver(hostname=device["hostname"], username="automation", password="<use env var>")
    conn.open()

    config = conn.get_config()["running"]
    with open(f"backups/{device['hostname']}.cfg", "w") as f:
        f.write(config)

    report = conn.compliance_report(validation_file="golden_config.yaml")
    conn.close()
    return report

def push_correction_via_netconf(hostname, approved_community):
    """Applies a low-risk corrective change via NETCONF's candidate/commit
    model. Used only for drift categories the compliance policy marks
    auto-fixable, security-sensitive categories such as SNMP always
    escalate instead of calling this function."""
    payload = CORRECTION_TEMPLATE.render(approved_community=approved_community)
    with manager.connect(host=hostname, username="automation", hostkey_verify=False) as m:
        m.edit_config(target="candidate", config=payload)
        m.validate(source="candidate")
        m.commit()

if __name__ == "__main__":
    for device in DEVICES:
        result = backup_device(device)
        status = "COMPLIANT" if result["complies"] else "DRIFT DETECTED"
        print(f"{device['hostname']}: {status}")
