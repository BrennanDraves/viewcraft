from dataclasses import dataclass


@dataclass
class SearchSpec:
    field: str
    lookup_type: str = 'contains'  # TODO: Make this a constant of some kind

    def get_lookup_string(self) -> str:
        """Returns the Django-style lookup string (e.g., 'title__contains')"""
        if self.lookup_type == 'exact':
            return self.field
        return f"{self.field}__{self.lookup_type}"
