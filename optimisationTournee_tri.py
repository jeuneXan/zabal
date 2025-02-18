import os
import requests
from datetime import datetime, timedelta
from dateutil.parser import parse


from authentification import get_api_session 
from utils import to_datetime

def is_workday(date_obj):
    """Retourne True si la date est un jour ouvré (lundi à vendredi)."""
    return date_obj.weekday() < 5  # 0 = lundi, 6 = dimanche

def add_workdays(start_date, workdays):
    """
    Ajoute un nombre de jours ouvrés à start_date.
    Exclut les week-ends (et éventuellement les jours fériés si ajoutés ultérieurement).
    """
    current_date = start_date
    added_days = 0
    while added_days < workdays:
        current_date += timedelta(days=1)
        if is_workday(current_date):
            added_days += 1
    return current_date

import requests

def get_poseur_ids():
    """
    Appelle l'API à l'URL spécifiée et récupère toutes les users du groupe "Poseur".
    
    Retourne une liste d'ID de poseurs.
    """
    base_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    endpoint = "/api/typeusers"  # Modifier si nécessaire
    url = f"{base_url}{endpoint}"


    try:
        # Obtenir la session API authentifiée
        session = get_api_session()
        # Faire la requête GET pour récupérer les rendez-vous
        response = session.get(url)
        response.raise_for_status()  # Gère les erreurs HTTP

        users = response.json()
        
        if not users:
            print("⚠️ L'API n'a retourné aucun rendez-vous !")
        
        poseurs = []
        for group in users:
            if group.get("nom", "").strip().lower() == "poseur":
                # Extraire les IDs de tous les users de ce groupe
                for user in group.get("users", []):
                    user_id = user.get("id")
                    if user_id is not None:
                        poseurs.append(user_id)
                break  # On s'arrête dès qu'on a trouvé le groupe "Poseur"
    
        return poseurs
    except requests.RequestException as e:
        return []


def get_gps(idChantier):
    """
    Appelle l'API à l'URL spécifiée et récupère toutes les users du groupe "Poseur".
    
    Retourne une liste d'ID de poseurs.
    """
    base_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    endpoint = "/api/chantiers/" + str(idChantier)  # Modifier si nécessaire
    url = f"{base_url}{endpoint}"
    try:
        # Obtenir la session API authentifiée
        session = get_api_session()
        # Faire la requête GET pour récupérer les rendez-vous
        response = session.get(url)
        response.raise_for_status()  # Gère les erreurs HTTP

        chantier = response.json()
        
        if not chantier:
            print("⚠️ L'API n'a retourné aucun rendez-vous !")
        
        gps=chantier.get("gps")
    
        return gps
    except requests.RequestException as e:
        return []


def call_disc_api(date_start: datetime, date_end: datetime):
    base_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    endpoint = "/api/rvinterventions/by-dates?datestart=17/02/2025&dateend=17/02/2025"  # Modifier si nécessaire
    url = f"{base_url}{endpoint}"


    try:
        # Obtenir la session API authentifiée
        session = get_api_session()
        # Faire la requête GET pour récupérer les rendez-vous
        response = session.get(url)
        response.raise_for_status()  # Gère les erreurs HTTP

        interventions = response.json()
        
        if not interventions:
            print("⚠️ L'API n'a retourné aucun rendez-vous !")
        
        return interventions
    except requests.RequestException as e:
        return []  # Retourne une liste vide en cas d'erreur




def filter_and_transform_intervention(interv, opt_start, opt_end):
    """
    Applique le filtrage et la transformation sur une intervention issue de l'API DISC.
    
    opt_start, opt_end : la plage d'optimisation calculée (objet datetime)

    Retourne un dictionnaire structuré selon les spécifications ou None si le rendez-vous est exclu.
    """

    # --- 1. Déterminer la plage de date pertinente selon le statut ---
    statusrv = interv.get("statusrv", "").lower()
    if statusrv in ["proposé", "convenu"]:
        # Si modifiable, on utilise daterv et datervfin
        date_debut_val = interv.get("daterv")
        date_fin_val   = interv.get("datervfin")
        modifiable = 0
        # Pour l'affectation des ressources, on utilisera "users"
        ressources = [user.get("id") for user in interv.get("user", [])]
    else:
        # Sinon, utiliser datevoulueclientde et datevoulueclienta
        date_debut_val = interv.get("datevoulueclientde")
        date_fin_val   = interv.get("datevoulueclienta")
        # Si les dates sont absentes ou vides, on utilise la plage d'optimisation
        if not date_debut_val or (isinstance(date_debut_val, str) and not date_debut_val.strip()):
            date_debut_val = opt_start
        if not date_fin_val or (isinstance(date_fin_val, str) and not date_fin_val.strip()):
            date_fin_val = opt_end
        modifiable = 1
        # Pour l'affectation des ressources, on utilisera "user_recommanded"
        if interv.get("user_recommanded") :
            ressources = [user.get("id") for user in interv.get("user_recommanded", [])]
        else :
            ressources=get_poseur_ids()

    # --- 2. Conversion des dates en objets datetime ---
    rdv_start = to_datetime(date_debut_val)
    rdv_end   = to_datetime(date_fin_val)

    if rdv_start is None or rdv_end is None:
        print(f"Erreur: Impossible de convertir les dates pour l'intervention {interv.get('id')}.")
        return None

    # --- 3. Vérifier l'intersection de l'intervalle du rendez-vous avec la plage d'optimisation ---
    if rdv_end < opt_start or rdv_start > opt_end:
        return None  # Pas d'intersection

    # --- 4. (Filtrage sur le contrôle des supports peut être ajouté ici) ---

    # --- 5. (Filtrage sur l'accessibilité du chantier peut être ajouté ici) ---

    # --- 6. Filtrage sur les marchandises ---
    marchandises = interv.get("marchandises", [])
    effective_start = rdv_start  # La date de début effective initiale est celle du rendez-vous
    if marchandises:
        for march in marchandises:
            status_march = march.get("statusmarchandise", {}).get("nom", "")
            if status_march in ["Réceptionné", "Livré"]:
                continue
            elif status_march == "Commandé":
                dateARC_val = march.get("dateARC")
                dateARC = to_datetime(dateARC_val)
                if dateARC is None and statusrv not in ["proposé", "convenu"]:
                    print(f"Erreur de conversion de dateARC pour l'intervention {interv.get('id')}.")
                    return None
                # Pour comparer, on rend les datetime naïfs
                dateARC_naive = dateARC.replace(tzinfo=None) if dateARC.tzinfo else dateARC
                opt_end_naive = opt_end.replace(tzinfo=None) if opt_end.tzinfo else opt_end
                if dateARC_naive > opt_end_naive and statusrv not in ["proposé", "convenu"]:
                    return None
                if dateARC_naive > effective_start and dateARC_naive <= opt_end_naive:
                    effective_start = dateARC_naive
            else:
                return None

    # --- 7. Transformation de l'intervention dans le format de sortie ---
    
    final_date_debut = effective_start.isoformat()
    final_date_fin   = rdv_end.isoformat()

    # --- 8. Filtre des rendez vous nous complétés ---
    gps = get_gps(interv.get("chantier", {}).get("id"))
    if not interv.get("nb_intervenants_mandatory") :
        nb_intervenants=1
    else:
        nb_intervenants=interv.get("nb_intervenants_mandatory")
    if (not gps or not interv.get("duree")) and statusrv not in ["proposé", "convenu"]:
        return None
    
    output = {
            "id_rdv": interv.get("id"),
            "modifiable": modifiable,
            "duree": interv.get("duree"),
            "nombre_ressources": nb_intervenants,
            "coordonnees_gps": gps,
            "affectation_ressources": ressources,
            "date_debut": final_date_debut,
            "date_fin": final_date_fin
        }
    return output



def optimisationTournee_tri(data):
    """
    Fonction de tri pour l'optimisation de la tournée.
    
    Paramètre d'entrée (data) :
      - Un dictionnaire contenant au moins le champ "nbJours" (nombre de jours ouvrés à optimiser).
    
    Étapes :
      1. Calcul de la plage d'optimisation :
         - Date de début = aujourd'hui.
         - Date de fin = aujourd'hui + nbJours ouvrés (excluant week-ends et, si possible, jours fériés).
      2. Appel GET à l'API du DISC (/rvinterventions) avec les paramètres "datedebut" et "datefin" (ISO 8601).
      3. Filtrage des interventions selon les critères :
         - Intersection partielle avec la plage d'optimisation.
         - Filtrage sur le contrôle ("control" doit être "Validé" ou "Validé à distance").
         - Filtrage sur l'accessibilité (champ "access_ask" non vide).
         - Filtrage sur les marchandises :
              * Si marchandises présentes : toutes doivent être "Réceptionné" ou "Livré", 
                ou, pour celles en "Commandé", leur "dateARC" doit être inférieure ou égale à la date de fin.
                De plus, si une "dateARC" est supérieure à la date de début, elle remplace la date de début.
      4. Structuration des interventions filtrées dans le format spécifié.
    
    Retour :
      - Une liste d'objets rendez-vous structurés.
    """
    nb_jours = data.get("nbJours", 0)
    if nb_jours <= 0:
        return []  # Aucun jour à optimiser, retourne liste vide

    # 1. Calcul de la plage d'optimisation
    today = datetime.now()
    # On fixe la date de début à aujourd'hui (en ignorant l'heure pour simplifier, si besoin vous pouvez conserver l'heure)
    opt_start = datetime(today.year, today.month, today.day)
    # Calculer la date de fin en ajoutant nb_jours ouvrés
    opt_end = add_workdays(opt_start, nb_jours)

    # 2. Appel à l'API du DISC

    jours_interventions = call_disc_api(opt_start, opt_end)
    


    # 3. Filtrage et transformation
    output_list = []
    for jour in jours_interventions :
        rvs = jour.get("rvs")
        for interv in rvs:
            transformed = filter_and_transform_intervention(interv, opt_start, opt_end)
            if transformed:
                output_list.append(transformed)
    return output_list

# Pour tester localement la fonction (optionnel)
#if __name__ == "__main__":
    # Exemple d'entrée : 5 jours ouvrés
 #   input_data = {"nbJours": 5}
  #  result = optimisationTournee_tri(input_data)
   # print(result)
