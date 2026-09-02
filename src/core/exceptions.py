class DuplicateRecordError(Exception):
    """Raised when a duplicate record exists."""
    pass


class RecordNotFoundError(Exception):
    """Raised when a record cannot be found."""
    pass


class BusinessRuleError(Exception):
    """Raised when a business rule is violated."""
    pass