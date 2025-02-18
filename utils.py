from datetime import datetime, timedelta

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