from rest_framework.serializers import Field, SlugRelatedField, ValidationError


class BaseSerializerContentTypeField(SlugRelatedField):
    """
    Field serializer for ContentType - the internal representation is an int
    The string representation is the concatenation of app + model, such as 'actions.session'
    """

    def to_representation(self, int_rep):
        return int_rep.app_label + "." + int_rep.model

    def to_internal_value(self, str_rep):
        """
        If there is no dot, attempt a straight model lookup that may have conflicts
        Otherwise look for 'app.model' syntax as is returned in the representation
        A good practice is to constrain the queryset when initializing the serializer to given apps
        to avoid conflicts on the model name as much as possible
        """
        if "." in str_rep:
            app, model = str_rep.split(".")
            obj = self.queryset.get(model=model, app_label=app)
        else:
            obj = self.queryset.get(model=str_rep)
        return obj


class BaseSerializerEnumField(Field):
    """
    Field serializer for an int model field with enumerated choices.
    This provides the string representation of the model for the rest requests and filters
    """

    @property
    def choices(self):
        if self.parent is None:
            raise ValueError("parent of {self} is None, canot access to choices")
        model = self.parent.Meta.model
        return model._meta.get_field(self.field_name).choices

    def to_representation(self, int_rep):
        status = [ch for ch in self.choices if ch[0] == int_rep]
        return status[0][1]

    def to_internal_value(self, str_rep):
        status = [ch for ch in self.choices if ch[1] == str_rep]
        if len(status) == 0:
            raise ValidationError(
                f"Invalid {self.field_name}, choices are: " + ", ".join([ch[1] for ch in self.choices])
            )
        return status[0][0]
