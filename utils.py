from datetime import datetime, timedelta
from dateutil.parser import parse

def to_datetime(val):
        # Si val est déjà un datetime, le retourner tel quel
        if isinstance(val, datetime):
            return val
        # Sinon, s'il s'agit d'une chaîne, tenter de la convertir
        elif isinstance(val, str):
            val = val.strip()
            if not val:
                return None
            try:
                # Si la chaîne contient "T", on suppose qu'il s'agit d'un format ISO 8601
                if "T" in val:
                    return datetime.fromisoformat(val)
                else:
                    # Sinon, tenter le format jour/mois/année
                    return datetime.strptime(val, "%d/%m/%Y")
            except ValueError:
                try:
                    # En dernier recours, utiliser dateutil.parser.parse qui est plus souple
                    return parse(val)
                except Exception as e:
                    print(f"Erreur de conversion de date '{val}': {e}")
                    return None
        else:
            return None
        
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