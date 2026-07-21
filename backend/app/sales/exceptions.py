class SalesDataError(Exception):
    """Base exception for all sales data-layer errors."""
    pass


class DatasetNotFoundError(SalesDataError):
    """Raised when the dataset directory or any CSV file inside it cannot be found."""
    pass


class SchemaValidationError(SalesDataError):
    """Raised when a CSV's columns cannot be mapped onto the required canonical sales schema."""
    pass


class EmptyDatasetError(SalesDataError):
    """Raised when a CSV has no usable rows left, either before or after cleaning."""
    pass
