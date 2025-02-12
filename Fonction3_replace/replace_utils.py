import json
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

def charger_rendez_vous(fichier="data/rendez_vous.json"):
    """Charge les rendez-vous depuis un fichier JSON."""
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement des rendez-vous : {e}")
        return []

def calculer_distance(coord1, coord2):
    """Calcule la distance entre deux points GPS (latitude, longitude) en km."""
    R = 6371  # Rayon moyen de la Terre en km
    lat1, lon1 = map(radians, map(float, coord1.split(",")))
    lat2, lon2 = map(radians, map(float, coord2.split(",")))

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # Distance en km

def distance_moyenne_avec_poseurs(candidat, dernier_rdv_poseur):
    """Calcule la distance moyenne entre le candidat et les derniers RDV des poseurs affectés."""
    distances = [
        calculer_distance(candidat["coordonnees_gps"], dernier_rdv_poseur[poseur]["coordonnees_gps"])
        for poseur in candidat["affectation_ressources"] if poseur in dernier_rdv_poseur
    ]
    return sum(distances) / len(distances) if distances else float("inf")  # Moyenne au lieu du min

def jours_ouvres(today, jours):
    """Retourne une liste des X prochains jours ouvrés à partir de today."""
    jours_ouvres = []
    date_courante = today
    while len(jours_ouvres) < jours:
        if date_courante.weekday() < 5:  # 0=Lundi, ..., 4=Vendredi
            jours_ouvres.append(date_courante)
        date_courante += timedelta(days=1)
    return jours_ouvres
