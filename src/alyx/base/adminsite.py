from django.contrib import admin
from django.contrib.admin import AdminSite
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from django.template.response import TemplateResponse

from .utils import Bunch, flatten
from .. import __version__

from typing import List, Literal, Optional, Iterator, Dict, Any

import structlog

logger = structlog.get_logger("base.adminsite")

ADMIN_PAGES = [
    (
        "Common",
        [
            "Subjects",
            "Cull_subjects",
            "Sessions",
            "Ephys sessions",
            "Surgeries",
            "Breeding pairs",
            "Litters",
            "Water administrations",
            "Water restrictions",
            "Weighings",
            "Subject requests",
        ],
    ),
    (
        "Data files",
        [
            "Data repository types",
            "Data repositories",
            "Data formats",
            "Dataset types",
            "Datasets",
            "Downloads",
            "File records",
            "Data collections",
            "Time series",
            "Event series",
            "Interval series",
            "Tags",
            "Revisions",
        ],
    ),
    (
        "Data that changes rarely",
        [
            "Lines",
            "Strains",
            "Alleles",
            "Sequences",
            "Sources",
            "Species",
            "Other actions",
            "Procedure types",
            "Water types",
            "Probe models",
        ],
    ),
    (
        "Other",
        [
            "Genotype tests",
            "Zygosities",
        ],
    ),
    (
        "IT admin",
        [
            "Tokens",
            "Groups",
            "Lab members",
            "Labs",
            "Lab locations",
            "Lab memberships",
        ],
    ),
]

ADDITIONAL_PAGES = [
    {"admin_url": "training", "name": "Training View", "perms": {}, "add_url": ""},
    {"admin_url": "management-hub", "name": "Management Hub", "perms": {}, "add_url": ""},
    {"admin_url": "services-hub", "name": "Services Hub", "perms": {}, "add_url": ""},
]


class ModelDict(Bunch):
    admin_url: str
    add_url: str
    name: str
    perms: dict
    object_name: str = ""


class Category(Bunch):
    models: List[ModelDict]
    name: str
    collapsed: Literal["", "collapsed"]
    app_label: str


class CategoryList(list):
    def __init__(self, categories: Optional[List[Category]] = None):
        if categories is None:
            categories = []
        super().__init__(categories)

    def append(self, category: Category) -> None:
        if not isinstance(category, Category):
            raise TypeError("Only Category instances can be added to CategoryList")
        super().append(category)

    def extend(self, categories: List[Category]) -> None:
        if not all(isinstance(category, Category) for category in categories):
            raise TypeError("All elements must be Category instances")
        super().extend(categories)

    def insert(self, index: int, category: Category) -> None:
        if not isinstance(category, Category):
            raise TypeError("Only Category instances can be inserted into CategoryList")
        super().insert(index, category)

    def __getitem__(self, index) -> Category:
        return super().__getitem__(index)

    def __iter__(self) -> Iterator[Category]:
        return super().__iter__()

    def named(self, name: str) -> Category:
        return self[[cat.name for cat in self].index(name)]


def get_showed_apps_list(app_list: List[Dict[str, Any]]):
    order = ADMIN_PAGES
    extra_in_common = ["Adverse effects", "Cull subjects"]

    def get_(model, app):
        logger.info(f'App:{app["name"]} model:{model["name"]}')
        return str(model["name"])

    models_dict = {get_(model, app): model for app in app_list for model in app["models"]}
    model_to_app = {str(model["name"]): str(app["name"]) for app in app_list for model in app["models"]}
    category_list = CategoryList(
        [
            Category(
                name=name,
                models=[ModelDict(models_dict[name]) for name in model_names if name in models_dict.keys()],
                collapsed="" if name == "Common" else "collapsed",
                app_label=name,
            )
            for name, model_names in order
        ]
    )
    models_in_order = flatten([models for app, models in order])
    for model_name, app_name in model_to_app.items():
        if model_name in models_in_order:
            logger.error(f"Could not register application {model_name}")
            continue
        if model_name.startswith("Subject") or model_name in extra_in_common:
            category_list.named("Common").models.append(models_dict[model_name])
        else:
            category_list.named("Other").models.append(models_dict[model_name])

    # Add link to training view in 'Common' panel.
    for page in ADDITIONAL_PAGES:
        model_dict = ModelDict(page.copy())
        model_dict["admin_url"] = reverse(model_dict["admin_url"])
        category_list.named("Common").models.append(model_dict)

    return category_list


class MyAdminSite(AdminSite):
    def index(self, request: WSGIRequest, extra_context=None):
        category_list = get_showed_apps_list(self.get_app_list(request))
        context = dict(
            self.each_context(request),
            title=self.index_title,
            app_list=category_list,
        )
        context["subtitle"] = ""
        context.update(extra_context or {})
        request.current_app = self.name  # type: ignore

        return TemplateResponse(request, self.index_template or "admin/index.html", context)


mysite = MyAdminSite()
mysite.site_header = "Alyx"
mysite.site_title = "Alyx"
mysite.site_url = ""
mysite.index_title = f"Welcome to Alyx {__version__}"
mysite.enable_nav_sidebar = False

admin.site = mysite
