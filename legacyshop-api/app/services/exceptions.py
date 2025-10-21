"""
Custom exceptions for business logic.
Mirrors the Java exception hierarchy.
"""


class BusinessValidationException(Exception):
    """Exception for business rule violations"""
    pass


class ResourceNotFoundException(Exception):
    """Exception for resource not found errors"""
    pass


class DuplicateResourceException(Exception):
    """Exception for duplicate resource errors"""
    pass


class PaymentException(Exception):
    """Exception for payment processing errors"""
    
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable
