from typing import List, Any

class FilterCriteriaDTO:
    def __init__(self, field: str, operation: str, value: Any):
        self.field = field
        self.operation = operation
        self.value = value

class FilterGroupDTO:
    def __init__(self, operator: str, groups: List[object], criterias: List[object]):
        self.operator = operator
        self.groups = groups
        self.criterias = criterias

class FiltersDTO:
    def __init__(self, fields: List[str], criterias: List[object], groups: List[object], operator: str):
        self.fields = fields
        self.criterias = criterias
        self.groups = groups
        self.operator = operator

