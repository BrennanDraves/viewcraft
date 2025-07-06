from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class SearchSpec:
    """
    Specification for a searchable field in the BasicSearchComponent.

    Attributes:
        field_name: Name of the model field
        lookup_types: List of supported Django lookup types for this field
        current_lookup_type: Currently selected lookup type
        field_type: Django field type name (e.g. "CharField", "DateField")
        extra_options: Additional options for custom field behavior
    """
    field_name: str
    lookup_types: List[str] = field(default_factory=lambda: ["contains"])
    current_lookup_type: Optional[str] = None
    field_type: str = "CharField"
    extra_options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default lookup type if none provided."""
        if self.current_lookup_type is None and self.lookup_types:
            self.current_lookup_type = self.lookup_types[0]

    def get_lookup_string(self) -> str:
        """
        Returns the Django-style lookup string (e.g., 'title__contains')

        Returns:
            str: Field name with lookup suffix if needed
        """
        lookup = self.current_lookup_type or self.lookup_types[0]

        # Special handling for range lookups
        if lookup == "range" and self.supports_range():
            # This will be handled specially in the component
            return self.field_name

        if lookup == 'exact':
            return self.field_name
        return f"{self.field_name}__{lookup}"

    def set_lookup_type(self, lookup_type: str) -> None:
        """
        Set the current lookup type if it's in the available lookup types.

        Args:
            lookup_type: The lookup type to set as current

        Raises:
            ValueError: If the lookup type is not in the available lookup types
        """
        if lookup_type in self.lookup_types:
            self.current_lookup_type = lookup_type
        else:
            raise ValueError(f"Lookup type '{lookup_type}' not in available lookup \
                             types: {self.lookup_types}")

    def supports_range(self) -> bool:
        """
        Check if this field supports range searches.

        Returns:
            bool: True if this field supports range searches
        """
        range_supporting_types = [
            "DateField", "DateTimeField",
            "IntegerField", "DecimalField", "FloatField"
        ]
        return (self.field_type in range_supporting_types and
                "range" in self.lookup_types)

    def is_choice_field(self) -> bool:
        """
        Check if this field should be rendered as a choice field.

        Returns:
            bool: True if this is a choice field
        """
        return 'choices' in self.extra_options

    def is_boolean_field(self) -> bool:
        """
        Check if this is a boolean field.

        Returns:
            bool: True if this is a boolean field
        """
        return self.field_type == 'BooleanField'
