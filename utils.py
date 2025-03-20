import math
from datetime import datetime, timedelta
from dateutil.parser import parse

from datetime import datetime, timezone
from dateutil.parser import parse

from datetime import datetime, timezone
from dateutil.parser import parse

def to_datetime(val):
    """
    Convertit une valeur (datetime ou chaîne) en un objet datetime en UTC.
    Le résultat est un datetime "aware" qui, lorsqu'il est affiché,
    ressemble à : "2025-02-07 09:29:44.799000+00:00".
    """
    if isinstance(val, datetime):
        dt = val
    elif isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        try:
            # Si la chaîne contient "T", on suppose un format ISO 8601
            if "T" in val:
                dt = datetime.fromisoformat(val)
            else:
                # Tenter le format "jour/mois/année"
                dt = datetime.strptime(val, "%d/%m/%Y")
        except ValueError:
            try:
                dt = parse(val)
            except Exception as e:
                print(f"Erreur de conversion de date '{val}': {e}")
                return None
    else:
        return None

    # Convertir en datetime aware en UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


       
def haversine_distance(coord1, coord2):
    """Calcule la distance (en km) entre deux points (lat, lon) avec la formule de Haversine."""
    R = 6371  # Rayon de la Terre en km
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c