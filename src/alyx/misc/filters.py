from ..base.filters import BaseFilterSet
from .models import Lab


class LabFilter(BaseFilterSet):
    pass

    class Meta:
        model = Lab
        exclude = ["json"]
