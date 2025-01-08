# Viewcraft

A modern, type-safe approach to composable Django class-based views.

## Features

- **Component-based**: Build views by composing reusable, self-contained components
- **Type-safe**: Full mypy support with strict type checking
- **Clean**: Linted to excess with Ruff
- **Zero config**: Components work out of the box with sensible defaults
- **Pluggable**: Easy to extend with your own components
- **Configurable**: Runtime configuration for maximum flexibility
- **Batteries included**: Common components like search and pagination built-in

## Installation

```bash
pip install viewcraft
```

Add to your installed apps in settings.py:

```python
INSTALLED_APPS = [
    ...
    'viewcraft',
]
```
]

## Quick Start

Sort your list of model objects without having to write your own queries or sort URLs:

```python
from django.views.generic import ListView
from viewcraft import ComponentMixin
from viewcraft.components import OrderingConfig

class UserListView(ComponentMixin, ListView):
    template_name = 'users/user_list.html'
    model = User

    components = [
        OrderingConfig(
            fields=['username', 'date_joined'],
            default_ordering='-date_joined'
        )
    ]
```

## Creating Custom Components

Components are easy to create and configure:

```python
from dataclasses import dataclass
from typing import TypeVar
from django.views import View
from viewcraft import BaseComponent, ComponentConfig, ComponentProtocol

ViewT = TypeVar('ViewT', bound=View)

@dataclass
class SortingConfig(ComponentConfig):
    fields: list[str]
    default_field: str

    def build_component(self, view: View) -> ComponentProtocol:
        return SortingComponent(view, self)

class SortingComponent(BaseComponent[ViewT]):
    def __init__(self, view: ViewT, config: SortingConfig) -> None:
        super().__init__(view)
        self.config = config

    def process_queryset(self, queryset: QuerySet) -> QuerySet:
        field = self.view.request.GET.get('sort', self.config.default_field)
        return queryset.order_by(field)
```

## Documentation

Full documentation is available at [Readthedocs](https://viewcraft.readthedocs.io/)
