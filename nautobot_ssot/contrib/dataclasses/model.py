"""Interface dataclass for connecting DiffSync"""

from dataclasses import dataclass, field
from nautobot_ssot.contrib.model import NautobotModel
from nautobot.core.models import BaseModel
from typing_extensions import Dict, get_type_hints
from nautobot_ssot.contrib.dataclasses.cache import ORMCache
from nautobot_ssot.contrib.dataclasses.attributes import AttributeInterface, attribute_interface_factory


@dataclass
class NautobotModelInterface:
    """Interface class for interacting with Nautobot ORM instances.
    
    This class manages the attributes and attribute interfaces for a given `NautobotModel` class. Since each
    `DiffSyncModel` class can vary between implementations, adapters should not interact attribute interfaces
    directly, but instead through this interface class only.
    """

    diffsync_class: NautobotModel
    cache: ORMCache = field(repr=False, default_factory=lambda : ORMCache())  # pylint: disable=unnecessary-lambda
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

    def get_attribute(self, db_obj: BaseModel, attribute: str):
        """Return the value of a single attribute given a ORM instance and attribute name."""
        return self.attribute_interfaces[attribute].load(db_obj)

    def get_attributes_dict(self, db_obj: BaseModel) -> Dict:
        """Return a dictionary of all parameters and their values for passed Nautobot Database Models."""
        parameters = {}
        for attribute_name, interface in self.attribute_interfaces.items():
            parameters[attribute_name] = interface.load(db_obj)
        return parameters
