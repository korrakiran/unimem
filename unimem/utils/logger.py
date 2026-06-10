"""Logging configuration utilizing the Rich library for beautiful terminal output."""

import logging
from rich.logging import RichHandler

def setup_logger(name: str = "unimem", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a styled logger using RichHandler."""
    logger = logging.getLogger(name)
    
    # If the logger is already configured, don't add handlers again
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # Clean up any existing handlers from root or inherited
    logger.propagate = False
    
    handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_path=False,
        markup=True
    )
    handler.setLevel(level)
    
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

# Shared default logger instance
logger = setup_logger()
