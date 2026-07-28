import openstack

def deploy_vm_stack(stack_name, template_path, parameters):
    conn = openstack.connect(cloud="telco-cloud")

    stack = conn.orchestration.create_stack(
        name=stack_name,
        template=open(template_path).read(),
        parameters=parameters
    )
    conn.orchestration.wait_for_status(stack, status="CREATE_COMPLETE")
    return conn.orchestration.get_stack(stack.id)

if __name__ == "__main__":
    result = deploy_vm_stack(
        stack_name="nfv-workload-purple-01",
        template_path="vm_stack.yaml",
        parameters={"flavor": "medium", "network": "tenant-net-purple"}
    )
    print(f"Stack {result.id} deployed with status {result.status}")
