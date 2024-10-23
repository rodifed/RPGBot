import s_taper
from s_taper.consts import *

users_scheme = {
    "user_id": INT+KEY,
    "name": TEXT,
    "power": TEXT,
    "hp": INT,
    "damage": INT,
    "score": INT,
    "level": INT
}

heals_scheme = {
    "user_id": INT+KEY,
    "food": TEXT
}

locations_scheme = {
    "user_id": INT+KEY,
    "money": INT,
    "animals": TEXT
}

users = s_taper.Taper("users", "db.db").create_table(users_scheme)
heals = s_taper.Taper("heals", "db.db").create_table(heals_scheme)
locations = s_taper.Taper("locations", "db.db").create_table(locations_scheme)