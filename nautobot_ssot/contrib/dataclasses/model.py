

from dataclasses import dataclass, field
from nautobot_ssot.contrib.model import NautobotModel
from nautobot.core.models import BaseModel
from typing_extensions import Dict, get_type_hints
from nautobot_ssot.contrib.dataclasses.cache import ORMCache
from nautobot_ssot.contrib.dataclasses.attributes import AttributeInterface, attribute_interface_factory


@dataclass
class NautobotModelInterface:
    """Interface class for interacting with Nautobot ORM instances."""

    diffsync_class: NautobotModel
    cache: ORMCache = field(repr=False, default_factory=lambda : ORMCache())
    attribute_interfaces: Dict[str, AttributeInterface] = field(repr=False, init=False)
    type_hints: dict = field(init=False, repr=False)

    def __post_init__(self):
        self.type_hints = get_type_hints(self.diffsync_class, include_extras=True)
        self.attribute_interfaces = {}
        for attribute in self.diffsync_class.get_parameters():
            self.attribute_interfaces[attribute] = attribute_interface_factory(
                name=attribute,
                type_hints=self.type_hints[attribute],
                model_class=self.diffsync_class._model,  # pylint: disable=protected-access
                cache=ORMCache,
            )

    @property
    def synced_attributes(self):
        """Return a list of synced attributes."""
        return self.attribute_interfaces.keys()

    def get_parameters(self, db_obj: BaseModel) -> Dict:
        """Return a dictionary of all parameters and their values for passed Nautobot Database Models."""
        parameters = {}
        for attribute_name, interface in self.attribute_interfaces.items():
            parameters[attribute_name] = interface.load(db_obj)
        return parameters
