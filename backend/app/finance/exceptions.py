class FinanceDataError(Exception):
    """Base exception for all finance data-layer errors."""
    pass


class DatasetNotFoundError(FinanceDataError):
    """Raised when the dataset directory or any CSV file inside it cannot be found."""
    pass


class SchemaValidationError(FinanceDataError):
    """Raised when a CSV's columns cannot be mapped onto the required canonical finance schema."""
    pass


class EmptyDatasetError(FinanceDataError):
    """Raised when a CSV has no usable rows left, either before or after cleaning."""
    pass
