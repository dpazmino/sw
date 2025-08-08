"""
Logging configuration and utilities
"""

import logging
import sys
from typing import Optional
from config import Config


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up logger with consistent formatting
    """
    config = Config()
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level
    log_level = level or config.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter(config.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


def setup_file_logger(name: str, filename: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up file logger
    """
    config = Config()
    
    # Create logger
    logger = logging.getLogger(f"{name}_file")
    
    # Set level
    log_level = level or config.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create file handler
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter(config.LOG_FORMAT)
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger


def log_performance(func):
    """
    Decorator to log function performance
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = setup_logger(f"performance.{func.__name__}")
        
        start_time = time.time()
        logger.debug(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {execution_time:.4f} seconds")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {str(e)}")
            raise
    
    return wrapper


def log_method_calls(cls):
    """
    Class decorator to log all method calls
    """
    import functools
    
    def log_calls(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            logger = setup_logger(f"{cls.__name__}.{func.__name__}")
            logger.debug(f"Calling {func.__name__} with args={len(args)}, kwargs={len(kwargs)}")
            
            try:
                result = func(self, *args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"{func.__name__} failed: {str(e)}")
                raise
        
        return wrapper
    
    # Apply decorator to all methods
    for attr_name, attr_value in cls.__dict__.items():
        if callable(attr_value) and not attr_name.startswith('_'):
            setattr(cls, attr_name, log_calls(attr_value))
    
    return cls


def create_audit_logger(name: str) -> logging.Logger:
    """
    Create audit logger for compliance tracking
    """
    logger = logging.getLogger(f"audit.{name}")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create audit file handler
    audit_handler = logging.FileHandler(f"data/audit_{name}.log")
    audit_handler.setLevel(logging.INFO)
    
    # Special audit formatter
    audit_formatter = logging.Formatter(
        '%(asctime)s - AUDIT - %(name)s - %(message)s'
    )
    audit_handler.setFormatter(audit_formatter)
    
    logger.addHandler(audit_handler)
    
    return logger


# Create module-level loggers
performance_logger = setup_logger("performance")
security_logger = setup_logger("security")
audit_logger = create_audit_logger("transactions")
