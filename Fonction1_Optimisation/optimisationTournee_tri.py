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
    date_start_call = date_start.strftime("%d/%m/%Y")
    date_end_call = date_end.strftime("%d/%m/%Y")
    base_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    endpoint = f"/api/rvinterventions/by-dates?datestart={date_start_call}&dateend={date_end_call}"  # Modifier si nécessaire
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

    # --- 1. Déterminer le statut et la modifiabilité ---
    if interv.get("dateProposedToClient") == 1 and interv.get("dateValidatedWithClient") == 0 :
        statusrv="proposé"
    elif interv.get("dateValidatedWithClient") == 0 :
        statusrv="convenu"
    else :
        statusrv="modifiable"

    if statusrv in ["proposé", "convenu"]:
        modifiable = 0
        # Pour l'affectation des ressources, on utilisera "users"
        ressources = [user.get("id") for user in interv.get("users", [])]
    else:
        modifiable = 1
        # Pour l'affectation des ressources, on utilisera "user_recommanded" si présent sinon la liste des poseurs
        if interv.get("user_recommanded"):
            ressources = [user.get("id") for user in interv.get("user_recommanded", [])]
        else:
            ressources = get_poseur_ids()

    # --- 2. Extraction des dates depuis l'API ---
    # Dates de rendez-vous (toujours issues de "daterv" et "datervfin")
    rdv_date_debut_val = interv.get("daterv")
    rdv_date_fin_val   = interv.get("datervfin")
    # Dates client (toujours issues de "datevoulueclientde" et "datevoulueclienta")
    client_date_debut_val = interv.get("datevoulueclientde")
    client_date_fin_val   = interv.get("datevoulueclienta")

    # Conversion en datetime
    rdv_start = to_datetime(rdv_date_debut_val)
    rdv_end   = to_datetime(rdv_date_fin_val)
    client_start = to_datetime(client_date_debut_val) if client_date_debut_val and str(client_date_debut_val).strip() else None
    client_end   = to_datetime(client_date_fin_val) if client_date_fin_val and str(client_date_fin_val).strip() else None

    opt_start_std = to_datetime(opt_start)
    opt_end_std   = to_datetime(opt_end)

    # --- 3. Vérification de l'intersection avec la plage d'optimisation ---
    # Vérification de l'intervalle rdv
    rdv_intersect = False
    if rdv_start and rdv_end:
        rdv_intersect = not (rdv_end < opt_start_std or rdv_start > opt_end_std)
        print("rdvinter",rdv_intersect, (rdv_end < opt_start_std or rdv_start > opt_end_std))

    # Vérification de l'intervalle client (seulement si les deux dates sont présentes)
    client_intersect = False
    if client_start and client_end:
        client_intersect = not (client_end < opt_start_std or client_start > opt_end_std)

    # L'intervention est conservée s'il y a intersection sur l'un ou l'autre des intervalles
    if not (rdv_intersect or client_intersect):
        print("sortie1", interv.get("id") ,rdv_end, opt_start_std, rdv_start, opt_end_std, client_end, client_start)
        return None

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
                if not dateARC_val:
                    dateARC_val = datetime.datetime.now()
                dateARC = to_datetime(dateARC_val)
                if dateARC is None and statusrv not in ["proposé", "convenu"]:
                    print(f"Erreur de conversion de dateARC pour l'intervention {interv.get('id')}.")
                    print("sortie2")
                    return None
                # Pour comparer, on rend les datetime naïfs
                dateARC_naive = dateARC.replace(tzinfo=None) if dateARC and dateARC.tzinfo else dateARC
                opt_end_naive = opt_end.replace(tzinfo=None) if opt_end.tzinfo else opt_end
                effective_start_naive = effective_start.replace(tzinfo=None) if effective_start.tzinfo else effective_start
                if dateARC_naive > opt_end_naive and statusrv not in ["proposé", "convenu"]:
                    print("sortie3")
                    return None
                if dateARC_naive > effective_start_naive and dateARC_naive <= opt_end_naive:
                    effective_start = dateARC
            else:
                print("sortie4")
                return None

    # --- 7. Transformation de l'intervention dans le format de sortie ---
    final_date_debut_rdv = rdv_start.isoformat() if rdv_start else None
    final_date_fin_rdv   = rdv_end.isoformat() if rdv_end else None
    final_date_debut_client = client_start.isoformat() if client_start else None
    final_date_fin_client   = client_end.isoformat() if client_end else None

    # --- 8. Filtre des rendez-vous non complétés ---

    gps = get_gps(interv.get("chantier", {}).get("id"))
    if not interv.get("nb_intervenants_mandatory"):
        nb_intervenants = 1
    else:
        nb_intervenants = interv.get("nb_intervenants_mandatory")
    if (not gps or not interv.get("duree")) and statusrv not in ["proposé", "convenu"]:
        print("sortie5")
        return None

    output = {
        "id_rdv": interv.get("id"),
        "modifiable": modifiable,
        "duree": interv.get("duree"),
        "nombre_ressources": nb_intervenants,
        "coordonnees_gps": gps,
        "affectation_ressources": ressources,
        "date_debut_rdv": final_date_debut_rdv,
        "date_fin_rdv": final_date_fin_rdv,
        "date_debut_client": final_date_debut_client,
        "date_fin_client": final_date_fin_client
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
    unique_interventions = {}
    for jour in jours_interventions:
        rvs = jour.get("rvs", [])
        for interv in rvs:
            transformed = filter_and_transform_intervention(interv, opt_start, opt_end)
            if transformed:
             unique_interventions[transformed["id_rdv"]] = transformed
    return list(unique_interventions.values())



# Pour tester localement la fonction (optionnel)
#if __name__ == "__main__":
    # Exemple d'entrée : 5 jours ouvrés
 #   input_data = {"nbJours": 5}
  #  result = optimisationTournee_tri(input_data)
   # print(result)
