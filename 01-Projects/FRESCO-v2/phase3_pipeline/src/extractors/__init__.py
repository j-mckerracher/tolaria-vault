"""FRESCO v2.0 Transformation Pipeline - Extractors"""

from .base import BaseExtractor
from .anvil import AnvilExtractor
from .conte import ConteExtractor
from .stampede import StampedeExtractor

__all__ = ['BaseExtractor', 'AnvilExtractor', 'ConteExtractor', 'StampedeExtractor']
