"""
Panch Pakshi Data Tables

Contains all the traditional sequences, ratings, and relationship tables
used in Panch Pakshi calculations.
"""

# Bird and activity representations
BIRD_EMOJIS = {
    'Crow': '🐦',
    'Cock': '🐓', 
    'Peacock': '🦚',
    'Vulture': '🦅',
    'Owl': '🦉'
}

ACTIVITY_EMOJIS = {
    'Ruling': '👑',
    'Eating': '🍽️',
    'Walking': '🚶',
    'Sleeping': '💤',
    'Dying': '💀'
}

ACTIVITY_COLORS = {
    'Ruling': '#388e3c',
    'Eating': '#43a047',
    'Walking': '#fbc02d',
    'Sleeping': '#757575',
    'Dying': '#c62828'
}

# Rating system mapping
RATING_MAP = {
    'very good': '++++++++',
    'good': '++++++',
    'average': '++++',
    'bad': '++',
    'very bad': '+'
}

# Core bird sequences for different paksha and day/night combinations
BIRD_SEQUENCES = {
    ('Shukla', 'Day'): ['Vulture', 'Owl', 'Crow', 'Cock', 'Peacock'],
    ('Shukla', 'Night'): ['Vulture', 'Peacock', 'Cock', 'Crow', 'Owl'],
    ('Krishna', 'Day'): ['Vulture', 'Crow', 'Peacock', 'Owl', 'Cock'],
    ('Krishna', 'Night'): ['Vulture', 'Cock', 'Owl', 'Peacock', 'Crow'],
}

# Activity orders with durations in minutes
ACTIVITY_ORDERS = {
    ('Shukla', 'Day'): [('Eating', 30), ('Walking', 36), ('Ruling', 48), ('Sleeping', 18), ('Dying', 12)],
    ('Shukla', 'Night'): [('Eating', 30), ('Ruling', 48), ('Dying', 12), ('Walking', 36), ('Sleeping', 18)],
    ('Krishna', 'Day'): [('Eating', 30), ('Dying', 12), ('Sleeping', 18), ('Ruling', 48), ('Walking', 36)],
    ('Krishna', 'Night'): [('Eating', 30), ('Sleeping', 18), ('Walking', 36), ('Dying', 12), ('Ruling', 48)],
}

# Ruling birds for each day of the week
RULING_DAYS_TABLE = {
    'Shukla': {
        'Day': {
            'Sunday': 'Vulture',
            'Monday': 'Owl',
            'Tuesday': 'Vulture',
            'Wednesday': 'Owl',
            'Thursday': 'Crow',
            'Friday': 'Cock',
            'Saturday': 'Peacock'
        },
        'Night': {
            'Sunday': 'Crow',
            'Monday': 'Cock',
            'Tuesday': 'Crow',
            'Wednesday': 'Crow',
            'Thursday': 'Peacock',
            'Friday': 'Vulture',
            'Saturday': 'Owl'
        }
    },
    'Krishna': {
        'Day': {
            'Sunday': 'Cock',
            'Monday': 'Peacock',
            'Tuesday': 'Cock',
            'Wednesday': 'Crow',
            'Thursday': 'Owl',
            'Friday': 'Vulture',
            'Saturday': 'Peacock'
        },
        'Night': {
            'Sunday': 'Vulture',
            'Monday': 'Vulture',
            'Tuesday': 'Crow',
            'Wednesday': 'Crow',
            'Thursday': 'Crow',
            'Friday': 'Peacock',
            'Saturday': 'Cock'
        }
    }
}

# Death birds for each day of the week
DEATH_DAYS_TABLE = {
    'Shukla': {
        'Day': {
            'Sunday': 'Owl',
            'Monday': 'Crow',
            'Tuesday': 'Cock',
            'Wednesday': 'Peacock',
            'Thursday': 'Vulture',
            'Friday': 'Owl',
            'Saturday': 'Vulture'
        },
        'Night': {
            'Sunday': 'Owl',
            'Monday': 'Crow',
            'Tuesday': 'Cock',
            'Wednesday': 'Peacock',
            'Thursday': 'Owl',
            'Friday': 'Owl',
            'Saturday': 'Vulture'
        }
    },
    'Krishna': {
        'Day': {
            'Sunday': 'Crow',
            'Monday': 'Owl',
            'Tuesday': 'Owl',
            'Wednesday': 'Vulture',
            'Thursday': 'Crow',
            'Friday': 'Peacock',
            'Saturday': 'Cock'
        },
        'Night': {
            'Sunday': 'Crow',
            'Monday': 'Owl',
            'Tuesday': 'Owl',
            'Wednesday': 'Vulture',
            'Thursday': 'Crow',
            'Friday': 'Peacock',
            'Saturday': 'Cock'
        }
    }
}

# Auspiciousness ratings for day activities
DAY_RATING = {
    'Peacock': {
        'Walking': 'good',
        'Ruling': 'average',
        'Sleeping': 'bad',
        'Dying': 'average',
        'Eating': 'good'
    },
    'Vulture': {
        'Walking': 'average',
        'Ruling': 'very good',
        'Sleeping': 'bad',
        'Dying': 'very bad',
        'Eating': 'good'
    },
    'Owl': {
        'Walking': 'good',
        'Ruling': 'good',
        'Sleeping': 'average',
        'Dying': 'bad',
        'Eating': 'average'
    },
    'Crow': {
        'Walking': 'very bad',
        'Ruling': 'good',
        'Sleeping': 'very bad',
        'Dying': 'very bad',
        'Eating': 'bad'
    },
    'Cock': {
        'Walking': 'very bad',
        'Ruling': 'very bad',
        'Sleeping': 'bad',
        'Dying': 'very bad',
        'Eating': 'good'
    }
}

# Auspiciousness ratings for night activities
NIGHT_RATING = {
    'Peacock': {
        'Walking': 'bad',
        'Ruling': 'very good',
        'Sleeping': 'average',
        'Dying': 'average',
        'Eating': 'average'
    },
    'Vulture': {
        'Walking': 'average',
        'Ruling': 'very good',
        'Sleeping': 'bad',
        'Dying': 'very bad',
        'Eating': 'good'
    },
    'Owl': {
        'Walking': 'average',
        'Ruling': 'average',
        'Sleeping': 'average',
        'Dying': 'bad',
        'Eating': 'very good'
    },
    'Crow': {
        'Walking': 'average',
        'Ruling': 'average',
        'Sleeping': 'average',
        'Dying': 'very bad',
        'Eating': 'very bad'
    },
    'Cock': {
        'Walking': 'average',
        'Ruling': 'average',
        'Sleeping': 'very bad',
        'Dying': 'very bad',
        'Eating': 'average'
    }
}

# Friend relationships between birds
FRIENDS = {
    'Shukla': {
        'Vulture': ['Peacock', 'Owl'],
        'Owl': ['Vulture', 'Crow'],
        'Crow': ['Owl', 'Cock'],
        'Cock': ['Crow', 'Peacock'],
        'Peacock': ['Cock', 'Vulture'],
    },
    'Krishna': {
        'Vulture': ['Crow', 'Peacock'],
        'Owl': ['Crow', 'Cock'],
        'Crow': ['Vulture', 'Owl'],
        'Cock': ['Crow', 'Peacock'],
        'Peacock': ['Cock', 'Vulture'],
    }
}

# Enemy relationships between birds
ENEMIES = {
    'Shukla': {
        'Vulture': ['Crow', 'Cock'],
        'Owl': ['Cock', 'Peacock'],
        'Crow': ['Peacock', 'Vulture'],
        'Cock': ['Vulture', 'Owl'],
        'Peacock': ['Owl', 'Crow'],
    },
    'Krishna': {
        'Vulture': ['Owl', 'Cock'],
        'Owl': ['Vulture', 'Peacock'],
        'Crow': ['Cock', 'Peacock'],
        'Cock': ['Vulture', 'Owl'],
        'Peacock': ['Owl', 'Crow'],
    }
}

# Nakshatra-based birth bird mapping using traditional Pancha Pakshi formula
# Based on paksha (moon phase) and nakshatra number (1-27)
PAKSHA_BIRD_RANGES = {
    'Shukla': {
        # Shukla Paksha (Bright Half) - Regular order
        (1, 5): 'Vulture',    # Nakshatras 1-5
        (6, 11): 'Owl',       # Nakshatras 6-11  
        (12, 16): 'Crow',     # Nakshatras 12-16
        (17, 21): 'Cock',     # Nakshatras 17-21
        (22, 27): 'Peacock',  # Nakshatras 22-27
    },
    'Krishna': {
        # Krishna Paksha (Dark Half) - Reverse order according to your formula
        (22, 27): 'Vulture',  # Nakshatras 27-22 (reverse)
        (17, 21): 'Owl',      # Nakshatras 21-17 (reverse) 
        (12, 16): 'Crow',     # Nakshatras 16-12 (reverse)
        (6, 11): 'Cock',      # Nakshatras 11-6 (reverse)
        (1, 5): 'Peacock',    # Nakshatras 5-1 (reverse)
    }
}

# Nakshatra details with start degrees (each nakshatra = 13°20')
NAKSHATRA_LIST = [
    ('Ashwini', 0.0),           # 1: 0° - 13°20'
    ('Bharani', 13.333),        # 2: 13°20' - 26°40'
    ('Krittika', 26.667),       # 3: 26°40' - 40°
    ('Rohini', 40.0),           # 4: 40° - 53°20'
    ('Mrigashira', 53.333),     # 5: 53°20' - 66°40'
    ('Ardra', 66.667),          # 6: 66°40' - 80°
    ('Punarvasu', 80.0),        # 7: 80° - 93°20'
    ('Pushya', 93.333),         # 8: 93°20' - 106°40'
    ('Ashlesha', 106.667),      # 9: 106°40' - 120°
    ('Magha', 120.0),           # 10: 120° - 133°20'
    ('Purva Phalguni', 133.333), # 11: 133°20' - 146°40'
    ('Uttara Phalguni', 146.667), # 12: 146°40' - 160°
    ('Hasta', 160.0),           # 13: 160° - 173°20'
    ('Chitra', 173.333),        # 14: 173°20' - 186°40'
    ('Swati', 186.667),         # 15: 186°40' - 200°
    ('Vishakha', 200.0),        # 16: 200° - 213°20'
    ('Anuradha', 213.333),      # 17: 213°20' - 226°40'
    ('Jyeshtha', 226.667),      # 18: 226°40' - 240°
    ('Mula', 240.0),            # 19: 240° - 253°20'
    ('Purva Ashadha', 253.333), # 20: 253°20' - 266°40'
    ('Uttara Ashadha', 266.667), # 21: 266°40' - 280°
    ('Shravana', 280.0),        # 22: 280° - 293°20'
    ('Dhanishta', 293.333),     # 23: 293°20' - 306°40'
    ('Shatabhisha', 306.667),   # 24: 306°40' - 320°
    ('Purva Bhadrapada', 320.0), # 25: 320° - 333°20'
    ('Uttara Bhadrapada', 333.333), # 26: 333°20' - 346°40'
    ('Revati', 346.667),        # 27: 346°40' - 360°
]

# Default location coordinates (Mumbai, India)
DEFAULT_LOCATION = {
    'name': 'Mumbai',
    'country': 'India',
    'timezone': 'Asia/Kolkata',
    'latitude': 19.0760,
    'longitude': 72.8777
}
