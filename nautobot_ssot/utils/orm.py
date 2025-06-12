
"""Helper functions for SSoT."""

from pydantic import validate_call

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from nautobot.extras.models import Relationship
from typing_extensions import TypedDict, get_type_hints, Type, is_typeddict

from nautobot_ssot.contrib.types import (
    RelationshipSideEnum,
)
from diffsync.exceptions import ObjectCrudException
from django.core.exceptions import MultipleObjectsReturned

from typing_extensions import Dict, List, TypedDict, Type, Any, Union

from typing_extensions import is_typeddict

def get_related_attribute_value(attr_name: str, db_obj: Model) -> Any:
    """Get the value of a Django ORM foreign key attribute using the Django queryset format.

    Args:
        attr_name (str): Name of the foreign key attribute to retrieve using Django queryset format
          for foreign keys (`__`).
        db_obj (Model): An instance of a Django ORM model.

    Returns:
        `Any` object with the value of the specified foreign key attribute.

    Raises:
        ValueError: An error occured when `attr_name` is not referencing a foreign key.
        TypeError: When the `db_obj` is not a child instance of the Django ORM.
    """
    if "__" not in attr_name:
        raise ValueError(f"Attribute `{attr_name}` is not a foreign key.")
    if not isinstance(db_obj, Model):
        raise TypeError(f"{db_obj} is not an instance of `django.db.models.Model`.")

    lookups = attr_name.split("__")
    related_attr_name = lookups.pop(-1)

    related_object = getattr(db_obj, lookups.pop(0))
    if not related_object:
        return None
    for lookup in lookups:
        related_object = getattr(related_object, lookup)
        if not related_object:
            return None
    # After all lookups are retrieved, get the value from the final related object
    return getattr(related_object, related_attr_name)


def load_typed_dict(typed_dict_class: Type, db_obj: Model) -> dict:
    """Convert a Django ORM object into an associated TypedDict.
    """
    if not is_typeddict(typed_dict_class):
        raise TypeError(f"`typed_dict_class` must be a subclass of `TypedDict`.")
    typed_dict = {}
    for field_name in get_type_hints(typed_dict_class):
        typed_dict[field_name] = (
            get_related_attribute_value(field_name, db_obj) \
            if "__" in field_name \
            else getattr(db_obj, field_name)
        )
    return typed_dict








def lookup_and_set_foreign_key(foreign_keys, db_obj: Model, adapter):
    """
    Given a list of foreign keys as dictionaries, look up and set foreign keys on an object.

    Dictionary should be in the form of:
    [
        {"field_1": "value_1", "field_2": "value_2"},
        ...
    ]
    where each item in the list corresponds to the parameters needed to uniquely identify a foreign key object.
    """

    for field_name, related_model_dict in foreign_keys.items():
        related_model = related_model_dict.pop("_model_class")
        # Generic foreign keys will not have this dictionary field. As such, we need to retrieve the appropriate
        # model class through other means.
        if not related_model:
            try:
                app_label = related_model_dict.pop("app_label")
                model = related_model_dict.pop("model")
            except KeyError as error:
                raise ValueError(
                    f"Missing annotation for '{field_name}__app_label' or '{field_name}__model - this is required"
                    f"for generic foreign keys."
                ) from error
            try:
                related_model_content_type = adapter.get_from_orm_cache(
                    {"app_label": app_label, "model": model}, ContentType
                )
                related_model = related_model_content_type.model_class()
            except ContentType.DoesNotExist as error:
                raise ObjectCrudException(f"Unknown content type '{app_label}.{model}'.") from error
        # Set the foreign key to 'None' when none of the fields are set to anything
        if not any(related_model_dict.values()):
            setattr(db_obj, field_name, None)
            continue
        try:
            related_object = adapter.get_from_orm_cache(related_model_dict, related_model)
        except related_model.DoesNotExist as error:
            raise ObjectCrudException(
                f"Couldn't find '{related_model._meta.verbose_name}' instance behind '{field_name}' with: {related_model_dict}."
            ) from error
        except MultipleObjectsReturned as error:
            raise ObjectCrudException(
                f"Found multiple instances for {field_name} wit: {related_model_dict}"
            ) from error
        setattr(db_obj, field_name, related_object)








class CustomRelationshipParameters(TypedDict):
    """Typed dict for custom relationship parameters."""

    relationship: str
    source_type: ContentType
    destination_type: ContentType


def get_relationship_parameters(obj: Model, relationship: Relationship, relationship_side: RelationshipSideEnum):
    """Get custom relationship parameters as dictionary.

    Parameters:
        obj (Model): Django ORM model instance, must be an instance of the specified side of the relationship.
        relationship (Relationship): Relationship instance from Nautobot ORM.
        relationship_side (RelationshipSideEnum): Instance of the `RelationshipSideEnum` class indicating which side
            ofthe relationship the passed object is.

    """
    relationship_association_parameters = {
        "relationship": relationship,
        "source_type": relationship.source_type,
        "destination_type": relationship.destination_type,
    }

    if relationship_side == RelationshipSideEnum.SOURCE:
        relationship_association_parameters["source_id"] = obj.id
    else:
        relationship_association_parameters["destination_id"] = obj.id
    return relationship_association_parameters
