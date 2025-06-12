

from nautobot_ssot.utils.orm import (
    load_typed_dict,
    get_related_attribute_value,
)
from django.test import TestCase
from nautobot.dcim.models import Location, LocationType
from typing_extensions import Optional
from unittest import skip
from typing_extensions import TypedDict
from nautobot.extras.models import Status


class BaseTestCase(TestCase):

    def setUp(self):
        """Set up the unittests."""
        status = Status.objects.get(name="Active")
        self.location_type_1 = LocationType.objects.create(
            name="Location Type 1",
        )
        self.location_type_2 = LocationType.objects.create(
            name="Location Type 2",
            description="Test Location",
            parent=self.location_type_1
        )
        self.location_1 = Location.objects.create(
            name="Location 1",
            location_type=self.location_type_1,
            status=status,
        )
        self.location_2 = Location.objects.create(
            name="Location 2",
            location_type=self.location_type_2,
            parent=self.location_1,
            status=status,
        )


class TestGetRelatedAttributeValue(BaseTestCase):
    """Unit tests for `get_related_attribute_value` function."""

    #################################################
    # ERROR RAISING
    #################################################

    def test_invalid_attribute_lookup(self):
        """Test with attribute name that doesn't exist in the ORM object."""
        with self.assertRaises(AttributeError):
            get_related_attribute_value("parent__invalid_attribute", self.location_2)

    def test_db_obj_input_type_str(self):
        """Test function with `db_obj` input type `str`."""
        with self.assertRaises(TypeError):
            get_related_attribute_value("parent__name", "string")

    def test_db_obj_input_type_int(self):
        """Test function with `db_obj` input type `int`."""
        with self.assertRaises(TypeError):
            get_related_attribute_value("parent__name", 42)

    def test_db_obj_input_type_dict(self):
        """Test function with `db_obj` input type `dict`."""
        with self.assertRaises(TypeError):
            get_related_attribute_value("parent__name", {"name": "Invalid", "parent__name": "Invalid Parent Name"})

    def test_attr_name_non_foreign_key(self):
        """Test function with `attr_name` referencing non-existent ORM object attribute."""
        with self.assertRaises(ValueError):
            get_related_attribute_value("name", self.location_2)

    def test_attr_name_input_type_int(self):
        """Test function with `attr_name` input type `int`."""
        with self.assertRaises(TypeError):
            get_related_attribute_value(42, self.location_1)

    def test_attr_name_input_type_orm_obj(self):
        """Test function with `attr_name` input type `Model`."""
        with self.assertRaises(TypeError):
            get_related_attribute_value(self.location_1, self.location_1)

    def test_attr_name_input_type_bool(self):
        """Test function with `attr_name` input type `bool`."""
        with self.assertRaises(TypeError):
            get_related_attribute_value(True, self.location_1)

    def test_attr_name_input_type_none(self):
        """Test function with `attr_name` input type `None`."""
        with self.assertRaises(TypeError):
            get_related_attribute_value(None, self.location_1)

    #################################################
    # SINGLE LEVEL LOOKUPS
    #################################################

    def test_single_level_lookup(self):
        """Test a single-level string lookup."""
        result = get_related_attribute_value("location_type__name", self.location_1)
        self.assertEqual(result, "Location Type 1")

    def test_single_level_none_result(self):
        """Test single level lookup with None result."""
        result = get_related_attribute_value("parent__name", self.location_1)
        self.assertIsNone(result)

    def test_single_level_blank_str_result(self):
        """Test single level lookup with blank string result."""
        result = get_related_attribute_value("location_type__description", self.location_1)
        self.assertEqual(result, "")

    def test_single_level_orm_object_return(self):
        """Test looking up single attribute when return type is ORM object."""
        result = get_related_attribute_value("parent__location_type", self.location_2)
        self.assertIsInstance(result, LocationType)

    #################################################
    # MULTI LEVEL LOOKUPS
    #################################################

    def test_multi_level_lookup(self):
        """Test a multi-level lookup."""
        result = get_related_attribute_value("parent__location_type__name", self.location_2)
        self.assertEqual(result, "Location Type 1")

    def test_multi_level_intermediate_none_result(self):
        """Test multi level lookup with None result."""
        result = get_related_attribute_value("parent__parent__location_type__name", self.location_2)
        self.assertIsNone(result)

    def test_multi_level_blank_str_result(self):
        """Test multi level lookup with blank string result."""
        result = get_related_attribute_value("parent__location_type__description", self.location_2)
        self.assertEqual(result, "")

    def test_multi_level_with_none_object(self):
        """Test multi level lookup with first related object as None."""
        result = get_related_attribute_value("parent__location_type__description", self.location_1)
        self.assertIsNone(result)

    def test_multi_level_with_empty_string_final_result(self):
        """Test multi level lookup where final attribute is None."""
        result = get_related_attribute_value("parent__location_type__description", self.location_2)
        self.assertEqual(result, "")


class TestLoadTypedDict(BaseTestCase):
    """"""

    class LocationTypeDict(TypedDict):
        """Test LocationType Typed Dict."""

        name: str
        description: Optional[str]
        parent__name: Optional[str]


    class LocationDict(TypedDict):
        """Test location TypedDict."""

        name: str
        location_type__name: str
        parent__name: Optional[str]
        description: Optional[str]
        parent__location_type__name: Optional[str]
        status__name: str


    def test_load_basic_location_type(self):
        """"""
        #raise ValueError(is_typeddict(LocationTypeDict))
        result = load_typed_dict(
            self.LocationTypeDict,
            self.location_type_1,
        )
        self.assertEqual(result["name"], "Location Type 1")
        self.assertEqual(result["description"], "")
        self.assertEqual(result["parent__name"], None)

    def test_load_basic_location(self):
        """"""
        result = load_typed_dict(
            self.LocationDict,
            self.location_1,
        )
        self.assertEqual(result["name"], "Location 1")
        self.assertEqual(result["description"], "")
        self.assertEqual(result["parent__name"], None)
        self.assertEqual(result["status__name"], "Active")

    def test_load_with_foreign_key(self):
        """"""
        result = load_typed_dict(
            self.LocationTypeDict,
            self.location_type_2,
        )
        self.assertEqual(result["name"], "Location Type 2")
        self.assertEqual(result["description"], "Test Location")
        self.assertEqual(result["parent__name"], "Location Type 1")

