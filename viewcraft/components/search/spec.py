from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchSpec:
    field_name: str
    lookup_types: List[str] = field(default_factory=lambda: ["contains"])
    current_lookup_type: Optional[str] = None

    def __post_init__(self):
        if self.current_lookup_type is None and self.lookup_types:
            self.current_lookup_type = self.lookup_types[0]

    def get_lookup_string(self) -> str:
        """Returns the Django-style lookup string (e.g., 'title__contains')"""
        lookup = self.current_lookup_type or self.lookup_types[0]
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
