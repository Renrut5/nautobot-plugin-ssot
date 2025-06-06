"""Base adapter module for interfacing with Nautobot in SSoT."""

from diffsync import Adapter
from django.db.models import Model
from nautobot_ssot.contrib.model import NautobotModel
from nautobot_ssot.contrib.dataclasses.cache import ORMCache
from nautobot_ssot.contrib.dataclasses.model import NautobotModelInterface


class NautobotAdapter(Adapter):
    """Adapter for loading data from Nautobot through the ORM.

    This adapter is able to infer how to load data from Nautobot based on how the models attached to it are defined.
    """

    def __init__(self, *args, job, sync=None, cache=ORMCache(), **kwargs):
        """Instantiate this class, but do not load data immediately from the local system."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.metadata_type = None
        self.metadata_scope_fields = {}
        self.cache=cache

    def load(self):
        if not hasattr(self, "top_level") or not self.top_level:
            raise AttributeError("'top_level' needs to be set as a class-level attribute.")
        for model_name in self.top_level:
            diffsync_model: NautobotModel = getattr(self, model_name)
            model_interface: NautobotModelInterface = NautobotModelInterface(
                diffsync_class=diffsync_model,
                cache=self.cache,
            )
            for db_obj in diffsync_model.get_queryset():
                self.add_nautobot_model(model_interface, db_obj)

    def add_nautobot_model(self, model_interface: NautobotModelInterface, db_obj: Model):
        self.add(
            **model_interface.get_attributes_dict(db_obj)
        )
