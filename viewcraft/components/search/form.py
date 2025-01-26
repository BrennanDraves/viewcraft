from typing import TYPE_CHECKING, Any

from django import forms

from .field import SearchOperator

if TYPE_CHECKING:
    from .component import SearchComponent

class SearchForm(forms.Form):
    def __init__(self, *args: Any, component: "SearchComponent", **kwargs: Any):
        super().__init__(*args, **kwargs)

        # Create fields dynamically based on component config
        for field_config in component.config.fields:
            field = field_config.field_class(
                label=field_config.display_text,
                required=False,
                **field_config.field_kwargs
            )
            self.fields[field_config.alias] = field

            # Add operator field if multiple operators available
            if len(field_config.operators) > 1:
                self.fields[f"{field_config.alias}_operator"] = forms.ChoiceField(
                    choices=[(op.value, op.value) for op in field_config.operators],
                    required=False,
                    initial=SearchOperator.CONTAINS.value
                )

    def get_query_string(self) -> str:
        """Convert form data to search query string."""
        if not self.is_valid():
            return ""

        parts = []
        for field_name, value in self.cleaned_data.items():
            if not value or field_name.endswith('_operator'):
                continue

            operator = self.cleaned_data.get(
                f"{field_name}_operator", SearchOperator.CONTAINS.value
            )
            parts.append(f"{field_name}:{operator}:{value}")

        return ','.join(parts)
