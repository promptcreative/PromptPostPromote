"""
Panch Pakshi - Five Bird Ephemeris Calculator

This package provides precise calculations for the ancient Tamil astrological
system of Panch Pakshi using Swiss Ephemeris and Astral libraries.
"""

__version__ = "1.0.0"
__author__ = "Panch Pakshi Calculator"
__description__ = "Precise Panch Pakshi calculations using Swiss Ephemeris"

from .calculator import PanchPakshiCalculator
from .ephemeris import EphemerisCalculator
from .data import *

__all__ = [
    'PanchPakshiCalculator',
    'EphemerisCalculator',
    'BIRD_SEQUENCES',
    'ACTIVITY_ORDERS',
    'RULING_DAYS_TABLE',
    'DEATH_DAYS_TABLE',
    'DAY_RATING',
    'NIGHT_RATING',
    'FRIENDS',
    'ENEMIES'
]
