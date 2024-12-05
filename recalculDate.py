from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2


# Fonction haversine pour calculer la distance entre deux points géographiques
def haversine(coord1, coord2):
    R = 6371  # Rayon moyen de la Terre en km
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


# Fonction pour caler le meilleur rendez-vous dans le créneau libre
def caler_meilleur_appointment(date_debut, date_fin, liste_appointments):
    # Convertir les dates en objets datetime
    print(date_debut)
    print(date_fin)
    date_debut = datetime.strptime(
        date_debut.split('.')[0] + "Z", "%Y-%m-%dT%H:%M:%SZ")
    date_fin = datetime.strptime(
        date_fin.split('.')[0] + "Z", "%Y-%m-%dT%H:%M:%SZ")
    temps_dispo_minutes = int((date_fin - date_debut).total_seconds() / 60)
    print(date_debut)
    print(date_fin)
    # Filtrer les rendez-vous répondant aux critères
    candidats = [
        appointment for appointment in liste_appointments
        if appointment['statut'] != "convenu" and appointment['accessibilite']
        == "libre" and appointment['duration'] <= temps_dispo_minutes and
        datetime.strptime(appointment['dateDispo'], "%Y-%m-%d") <= date_debut
        and (appointment['start'] is None or datetime.strptime(
            appointment['start'], "%Y-%m-%dT%H:%M:%S") >= date_debut)
    ]

    if not candidats:
        print("Aucun rendez-vous répondant aux critères.")
        return None

    # Filtrer les rendez-vous ayant des champs start et end valides
    valid_appointments = [
        appointment for appointment in liste_appointments
        if appointment['start'] is not None and appointment['end'] is not None
    ]

    # Trouver l'appointement avant et après le créneau
    before_appointment = max(
        (appointment
         for appointment in valid_appointments if datetime.strptime(
             appointment['end'], "%Y-%m-%dT%H:%M:%S") <= date_debut),
        key=lambda x: datetime.strptime(x['end'], "%Y-%m-%dT%H:%M:%S"),
        default=None)

    after_appointment = min(
        (appointment
         for appointment in valid_appointments if datetime.strptime(
             appointment['start'], "%Y-%m-%dT%H:%M:%S") >= date_fin),
        key=lambda x: datetime.strptime(x['start'], "%Y-%m-%dT%H:%M:%S"),
        default=None)

    # Calculer les distances pour chaque candidat
    meilleur_appointment = None
    meilleure_distance = float('inf')

    for candidat in candidats:
        distance_avant = haversine(
            before_appointment['geolocalisation'],
            candidat['geolocalisation']) if before_appointment else 0
        distance_apres = haversine(
            candidat['geolocalisation'],
            after_appointment['geolocalisation']) if after_appointment else 0
        distance_totale = distance_avant + distance_apres

        if distance_totale < meilleure_distance:
            meilleure_distance = distance_totale
            meilleur_appointment = candidat

    # Modifier les champs du meilleur rendez-vous pour l'ajuster au créneau libre
    if meilleur_appointment:
        meilleur_appointment['start'] = date_debut.strftime(
            "%Y-%m-%dT%H:%M:%S")
        meilleur_appointment['end'] = (
            date_debut + timedelta(minutes=meilleur_appointment['duration'])
        ).strftime("%Y-%m-%dT%H:%M:%S")
        print(f"Meilleur rendez-vous trouvé : {meilleur_appointment}")
        return meilleur_appointment

    return None


# Tester la fonction
if __name__ == "__main__":
    date_debut = "2024-12-02T11:30:00"
    date_fin = "2024-12-02T13:00:00"

    liste_appointments = [{
        "id": "1",
        "title": "Rendez-vous Client A",
        "start": "2024-12-02T10:00:00",
        "end": "2024-12-02T11:30:00",
        "duration": 90,
        "statut": "",
        "accessibilite": "libre",
        "geolocalisation": (48.8566, 2.3522),
        "dateDispo": "2024-11-29"
    }, {
        "id": "2",
        "title": "Rendez-vous Client B",
        "start": "2024-12-02T13:00:00",
        "end": "2024-12-02T14:30:00",
        "duration": 60,
        "statut": "convenu",
        "accessibilite": "libre",
        "geolocalisation": (48.8570, 2.3530),
        "dateDispo": "2024-12-01"
    }, {
        "id": "3",
        "title": "Rendez-vous Client C",
        "start": None,
        "end": None,
        "duration": 30,
        "statut": "",
        "accessibilite": "pas libre",
        "geolocalisation": (48.8580, 2.3540),
        "dateDispo": "2024-11-28"
    }, {
        "id": "3",
        "title": "Rendez-vous Client D",
        "start": None,
        "end": None,
        "duration": 30,
        "statut": "",
        "accessibilite": "libre",
        "geolocalisation": (48.8580, 3.3540),
        "dateDispo": "2024-11-28"
    }]

    meilleur = caler_meilleur_appointment(date_debut, date_fin,
                                          liste_appointments)
    print("Résultat :", meilleur)
