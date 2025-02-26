import json
import requests
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from authentification import get_api_session

def charger_rendez_vous(fichier="data/rendez_vous.json"):
    """
    Récupère les rendez-vous depuis l’API externe
    (exemple d’appel).
    """
    base_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    endpoint = "/api/rvinterventions/by-dates?datestart=24/02/2025&dateend=25/03/2025"
    url = f"{base_url}{endpoint}"

    try:
        session = get_api_session()
        response = session.get(url)
        response.raise_for_status()

        interventions = response.json()
        return interventions

    except requests.RequestException as e:
        print(f"❌ Erreur lors de l'appel à l'API : {e}")
        return []

def calculer_distance(coord1, coord2):
    """
    Calcule la distance (en km) entre 2 points GPS "lat,lon".
    """
    R = 6371
    lat1, lon1 = map(radians, map(float, coord1.split(",")))
    lat2, lon2 = map(radians, map(float, coord2.split(",")))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def distance_moyenne_avec_poseurs(rdv, dernier_rdv_poseur):
    """
    Ex: calcule la distance moyenne entre le chantier du RDV
    et le "dernier RDV" de chaque poseur, si on voulait.
    Ici, on le laisse simplifié.
    """
    gps_rdv = rdv.get("chantier", {}).get("gps", "")
    if not gps_rdv:
        return float("inf")
    return 0.0
