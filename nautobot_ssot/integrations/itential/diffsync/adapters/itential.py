"""Itential SSoT adapters."""

from diffsync import DiffSync
from nautobot_ssot.integrations.itential.diffsync.models.itential import ItentialAnsibleDeviceModel
from nautobot_ssot.integrations.itential.clients import AutomationGatewayClient


class ItentialAnsibleDeviceAdapter(DiffSync):
    """Itential Ansible Device Diffsync adapter."""

    device = ItentialAnsibleDeviceModel
    top_level = ["device"]

    def __init__(self, api_client: AutomationGatewayClient, job: object, *args, **kwargs):
        """Initialize Diffsync Adapter."""
        self.api_client = api_client
        self.job = job

    def load(self):
        """Load Adapter."""
        self.job.load_info(message=f"Loading Itential devices from {self.api_client.host} into Diffsync adapter.")
        devices = self.api_client.get_devices()

        for iag_device in devices:
            device_vars = iag_device.get("variables")
            _device = self.device(name=iag_device.get("name"), variables=device_vars)

            self.add(_device)
