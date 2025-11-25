"""
Middleware Package

Handles cross-cutting concerns like error logging, request tracking, etc.
"""

from app.middleware.error_logger import (
    log_error,
    generate_error_signature,
    should_trigger_repair,
    wrap_untrusted_log,
    sanitize_stack_trace
)

__all__ = [
    'log_error',
    'generate_error_signature',
    'should_trigger_repair',
    'wrap_untrusted_log',
    'sanitize_stack_trace'
]
