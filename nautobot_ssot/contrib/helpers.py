
from collections import defaultdict


def relationship_fields_dict():
    """Return base relationship_fields dictionary."""
    return {
        # Example: {"group": {"name": "Group Name", "_model_class": TenantGroup}}
        "foreign_keys": defaultdict(dict),
        # Example: {"tags": [Tag-1, Tag-2]}
        "many_to_many_fields": defaultdict(list),
        # Example: TODO
        "custom_relationship_foreign_keys": defaultdict(dict),
        # Example: TODO
        "custom_relationship_many_to_many_fields": defaultdict(dict),
    }
