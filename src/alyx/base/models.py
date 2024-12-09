from django.db.models import Model, UUIDField, CharField, JSONField
from polymorphic.models import PolymorphicModel
import uuid


class BaseModel(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(max_length=255, blank=True, help_text="Long name")
    json = JSONField(
        null=True,
        blank=True,
        help_text="Structured data, formatted in a user-defined way",
    )

    class Meta:
        abstract = True


class BasePolymorphicModel(PolymorphicModel):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    json = JSONField(
        null=True,
        blank=True,
        help_text="Structured data, formatted in a user-defined way",
    )

    class Meta:
        abstract = True


class CharNullField(CharField):
    """
    Subclass of the CharField that allows empty strings to be stored as NULL.

    This allows for unique assertions on non-empty string fields only.

    See this URL:
    https://stackoverflow.com/questions/454436/unique-fields-that-allow-nulls-in-django/1934764
    """

    description = "CharField that stores NULL but returns ''."

    def from_db_value(self, value, *_):
        """
        Gets value right out of the db and changes it if it's None.
        """
        return value or ""

    def to_python(self, value):
        """
        Gets value right out of the db or an instance, and changes it if it's `None`.
        """
        if isinstance(value, CharField):
            # If an instance, just return the instance.
            return value
        if value is None:
            # If db has NULL, convert it to ''.
            return ""

        # Otherwise, just return the value.
        return value

    def get_prep_value(self, value):
        """
        Catches value right before sending to db.
        """
        if value == "":
            # If Django tries to save an empty string, send the db None (NULL).
            return None
        else:
            # Otherwise, just pass the value.
            return value


def modify_fields(**kwargs):
    def wrap(cls):
        for field, prop_dict in kwargs.items():
            for prop, val in prop_dict.items():
                setattr(cls._meta.get_field(field), prop, val)
        return cls

    return wrap
