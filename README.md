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
