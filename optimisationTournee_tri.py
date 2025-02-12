import os
import requests
from datetime import datetime, timedelta

from authentification import get_api_session 

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

import os
from authentification import get_api_session

def call_disc_api(date_debut, date_fin):
    """
    Appelle l'API du DISC pour récupérer les interventions.
    
    - L'URL de base est récupérée depuis la variable d'environnement DISC_API_URL,
      avec la valeur par défaut 'https://preprod.disc-chantier.com/api'.
    - L'endpoint est '/rvinterventions'.
    - Les paramètres envoyés sont 'datedebut' et 'datefin' au format ISO 8601.
    - Un header 'Accept: application/json' est ajouté pour demander une réponse JSON.
    
    Cette version affiche la requête effectuée ainsi que la réponse pour faciliter le débogage.
    """
    base_url = os.environ.get("DISC_API_URL", "https://preprod.disc-chantier.com/api")
    endpoint = "/rvinterventions"
    url = base_url + endpoint
    params = {
        "datedebut": date_debut.isoformat(),
        "datefin": date_fin.isoformat()
    }
    
    # Header par défaut pour obtenir du JSON
    headers = {"Accept": "application/json"}
    
    print("=== DÉBUT DE L'APPEL API DISC ===")
    print(f"URL: {url}")
    print(f"Paramètres: {params}")
    print(f"Headers envoyés: {headers}")
    
    try:
        # Récupère la session connectée (la connexion se fait une seule fois)
        session = get_api_session()
        # Effectue l'appel GET en utilisant la session (le cookie de session est automatiquement envoyé)
        response = session.get(url, params=params, headers=headers)
        
        # Affichage des informations sur la requête effectuée
        print("=== Requête effectuée ===")
        print(f"Méthode: {response.request.method}")
        print(f"URL complète de la requête: {response.request.url}")
        print(f"En-têtes de la requête: {response.request.headers}")
        
        # Affichage des informations sur la réponse
        print("=== Réponse reçue ===")
        print(f"Code de statut: {response.status_code}")
        print(f"En-têtes de la réponse: {response.headers}")
        print(f"Contenu de la réponse: {response.text}")
        
        # Lève une exception si le code de statut n'indique pas le succès (200-299)
        response.raise_for_status()
        
        interventions = response.json()
        print("=== Appel API réussi, données récupérées ===")
        return interventions
    except Exception as e:
        print(f"Erreur lors de l'appel à l'API DISC: {e}")
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
        date_debut_str = interv.get("daterv")
        date_fin_str   = interv.get("datervfin")
        modifiable = 0
        # Pour l'affectation des ressources, on utilisera "users"
        ressources = interv.get("users", [])
    else:
        # Sinon, utiliser datevoulueclientde et datevoulueclienta
        date_debut_str = interv.get("datevoulueclientde")
        date_fin_str   = interv.get("datevoulueclienta")
        modifiable = 1
        # Pour l'affectation des ressources, on utilisera "user_recommanded"
        ressources = interv.get("user_recommanded", [])

    # Convertir les dates en objets datetime
    try:
        # On suppose que les dates sont en ISO 8601
        rdv_start = datetime.fromisoformat(date_debut_str)
        rdv_end   = datetime.fromisoformat(date_fin_str)
    except Exception as e:
        print(f"Erreur de conversion de date pour l'intervention {interv.get('id')}: {e}")
        return None

    # --- 2. Vérifier l'intersection de l'intervalle du rendez-vous avec la plage d'optimisation ---
    # On considère qu'il y a intersection si rdv_end >= opt_start et rdv_start <= opt_end
    if rdv_end < opt_start or rdv_start > opt_end:
        return None  # Pas d'intersection

    # --- 3. Filtrage sur le contrôle des supports ---
    control = interv.get("control", "")
    if control not in ["Validé", "Validé à distance"]:
        return None

    # --- 4. Filtrage sur l'accessibilité du chantier ---
    access_ask = interv.get("access_ask")
    if not access_ask:
        return None

    # --- 5. Filtrage sur les marchandises ---
    marchandises = interv.get("marchandises", [])
    effective_start = rdv_start  # On pourra potentiellement modifier la date de début
    if marchandises:
        for march in marchandises:
            # Récupérer le statut de la marchandise (dans l'objet statusmarchandise, le champ "nom")
            status_march = march.get("statusmarchandise", {}).get("nom", "")
            if status_march in ["Réceptionné", "Livré"]:
                # OK pour cette marchandise
                continue
            elif status_march == "Commandé":
                # Comparer la dateARC à la plage d'optimisation
                dateARC_str = march.get("dateARC")
                try:
                    dateARC = datetime.fromisoformat(dateARC_str)
                except Exception as e:
                    print(f"Erreur de conversion de dateARC: {e}")
                    return None
                # Si dateARC > date de fin de la plage => exclure le rendez-vous
                if dateARC > opt_end:
                    return None
                # Si dateARC est supérieure à l'actuelle date de début, on met à jour effective_start
                if dateARC > effective_start and dateARC <= opt_end:
                    effective_start = dateARC
            else:
                # Statut non acceptable
                return None

    # --- 6. Transformation de l'intervention dans le format de sortie ---
    # Extraire la liste des noms des ressources
    affectation = [r.get("username") for r in ressources if "username" in r]

    # Choisir les dates à renvoyer (en format ISO 8601)
    # Si la date effective_start a été modifiée par un dateARC, l'utiliser
    final_date_debut = effective_start.isoformat()
    final_date_fin   = rdv_end.isoformat()

    # Construire l'objet de sortie
    output = {
        "rdv": {
            "id_rdv": interv.get("id"),
            "modifiable": modifiable,
            "duree": interv.get("duree"),
            "nombre_ressources": interv.get("nb_intervenants_mandatory"),
            "coordonnees_gps": interv.get("chantier", {}).get("gps"),
            "affectation_ressources": affectation,
            "date_debut": final_date_debut,
            "date_fin": final_date_fin
        }
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
    interventions = call_disc_api(opt_start, opt_end)

    # 3. Filtrage et transformation
    output_list = []
    for interv in interventions:
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
