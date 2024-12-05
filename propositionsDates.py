from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import holidays  # Bibliothèque pour gérer les jours fériés


# Fonction haversine
def haversine(coord1, coord2):
    R = 6371  # Rayon moyen de la Terre en km
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


# Fonction principale
def ajouter_dates(appointment, liste_appointments):
    required_keys = {
        'id',
        'title',
        'geolocalisation',
        'duration',
        'statut',
        'start',
        'end',
        'dateDispo',
    }
    if not all(key in appointment for key in required_keys):
        return "appointment incomplete"

    geoloc = appointment['geolocalisation']
    duree_intervention = timedelta(minutes=appointment['duration'])
    date_dispo = datetime.strptime(appointment['dateDispo'], "%Y-%m-%d")

    distance_seuil = 20
    jours_feries = holidays.France()

    # Filtrer les rendez-vous valides
    rendez_vous_valides = []
    for autre_appointment in liste_appointments:
        if not all(key in autre_appointment for key in required_keys):
            print(f"Objet incomplet ignoré : {autre_appointment}")
            continue
        if not autre_appointment['start'] or not autre_appointment['end']:
            print(f"Rendez-vous avec start/end vide ignoré : {autre_appointment}")
            continue

        rendez_vous_valides.append(autre_appointment)

    # Trouver les rendez-vous proches
    appointments_proches = []
    for autre_appointment in rendez_vous_valides:
        autre_geoloc = autre_appointment['geolocalisation']
        distance = haversine(geoloc, autre_geoloc)
        if distance <= distance_seuil:
            appointments_proches.append(autre_appointment)

    current_date = date_dispo
    end_date = date_dispo + timedelta(days=60)

    while current_date <= end_date:
        if current_date.weekday() < 5 and current_date not in jours_feries:
            # Trouver les rendez-vous prévus pour cette journée
            rendez_vous_du_jour = [
                autre_appointment for autre_appointment in appointments_proches
                if datetime.strptime(autre_appointment['start'], "%Y-%m-%dT%H:%M:%S").date() == current_date.date()
            ]
            print(f"Rendez-vous du jour trouvés ({current_date.date()}): {rendez_vous_du_jour}")

            if not rendez_vous_du_jour:
                jour_libre = all(
                    datetime.strptime(autre_appointment['start'], "%Y-%m-%dT%H:%M:%S").date() != current_date.date()
                    for autre_appointment in rendez_vous_valides
                )
                if jour_libre:
                    debut_potentiel = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=8)
                    fin_potentiel = debut_potentiel + duree_intervention
                    appointment['start'] = debut_potentiel.strftime("%Y-%m-%dT%H:%M:%S")
                    appointment['end'] = fin_potentiel.strftime("%Y-%m-%dT%H:%M:%S")
                    print(f"Aucun rendez-vous proche. Assigné à {debut_potentiel}")
                    return
            else:
                dernier_rendez_vous = max(
                    rendez_vous_du_jour,
                    key=lambda rdv: datetime.strptime(rdv['end'], "%Y-%m-%dT%H:%M:%S"),
                )
                dernier_fin = datetime.strptime(dernier_rendez_vous['end'], "%Y-%m-%dT%H:%M:%S")
                debut_potentiel = dernier_fin
                fin_potentiel = debut_potentiel + duree_intervention

                appointment['start'] = debut_potentiel.strftime("%Y-%m-%dT%H:%M:%S")
                appointment['end'] = fin_potentiel.strftime("%Y-%m-%dT%H:%M:%S")
                print(f"Dernier rendez-vous trouvé. Assigné à {debut_potentiel}")
                return

        current_date += timedelta(days=1)

    appointment['start'] = None
    appointment['end'] = None


# Tester la fonction lorsqu'on exécute le fichier
if __name__ == "__main__":
    appointments = {
        "id": 1,
        "title": "appointments1",
        "geolocalisation": (48.8566, 2.3522),
        "duration": 120,  # En minutes
        "statut": "",
        "start": None,
        "end": None,
        "dateDispo": "2024-11-02"
    }

    liste_appointments = [
        {
            "id": 2,
            "title": "appointments2",
            "geolocalisation": (48.8570, 2.3530),
            "duration": 60,
            "statut": "",
            "start": "2024-11-04 08:00:00",
            "end": "2024-11-04 09:00:00",
            "dateDispo": "2024-11-02"
        },
        {
            "id": 3,
            "title": "appointments3",
            "geolocalisation": (48.8666, 2.3522),
            "duration": 90,
            "statut": "",
            "start": None,  # Vide
            "end": "2024-11-04 10:30:00",
            "dateDispo": "2024-11-02"
        },
    ]

    ajouter_dates(appointments, liste_appointments)
    print("appointments après mise à jour :", appointments)
