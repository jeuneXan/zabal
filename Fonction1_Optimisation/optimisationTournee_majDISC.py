import os
import requests
from authentification import get_api_session 


base_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")


def update_intervention(intervention, session):
    """
    Met à jour une intervention via une requête PATCH.
    
    Paramètres :
      - intervention (dict) : un dictionnaire contenant les données de l'intervention, avec notamment :
          * "id_rdv" : l'identifiant utilisé dans l'URL
          * "affectation_ressources" : correspond au champ "users"
          * "date_debut" : correspond au champ "daterv" (format ISO 8601 attendu)
          * "date_fin" : correspond au champ "datervfin" (format ISO 8601 attendu)
      - session : la session requests configurée pour l'API
      
    Retour :
      - Le contenu JSON de la réponse API en cas de succès,
      - Sinon, un dictionnaire contenant l'erreur.
    """
    base_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    intervention_id = intervention.get("id_rdv")
    if intervention_id is None:
        return {"error": "Missing id_rdv in intervention", "intervention": intervention}
    
    url = f"{base_url}/api/rvinterventions/{intervention_id}"
    

    users_for_patch = [f"/api/users/{resource}" for resource in intervention.get('affectation_ressources')]

    payload = {
        "users": users_for_patch,
        "daterv": intervention.get("date_debut_rdv"),
        "datervfin": intervention.get("date_fin_rdv")
    }
    
    headers = {"Content-Type": "application/merge-patch+json"}
    print(url, payload, headers)
    try:
        response = session.patch(url, json=payload, headers=headers)
        response.raise_for_status()  # Génère une exception pour les codes d'erreur HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "id": intervention_id}

def update_interventions(interventions_list):
    """
    Itère sur une liste d'interventions et met à jour chacune d'elles via l'API.
    
    Paramètres :
      - interventions_list (list) : liste de dictionnaires d'interventions
      
    Retour :
      - Une liste contenant la réponse de l'API pour chaque intervention.
    """
    session = get_api_session()
    results = []
    for intervention in interventions_list:
        result = update_intervention(intervention, session)
        results.append(result)
    print(results)    
    return results

# Exemple d'utilisation
""""
if __name__ == "__main__":
    interventions = [
        {
            "id_rdv": 1234,
            "modifiable": True,
            "duree": 60,
            "nombre_ressources": 2,
            "coordonnees_gps": "48.8566,2.3522",
            "affectation_ressources": ["resource1", "resource2"],
            "date_debut": "2025-03-14T12:01:16.628Z",
            "date_fin": "2025-03-14T13:01:16.628Z"
        },
        {
            "id_rdv": 5678,
            "modifiable": True,
            "duree": 45,
            "nombre_ressources": 1,
            "coordonnees_gps": "48.8566,2.3522",
            "affectation_ressources": ["resource3"],
            "date_debut": "2025-03-15T12:01:16.628Z",
            "date_fin": "2025-03-15T12:46:16.628Z"
        }
    ]
    
    responses = update_interventions(interventions)
    print(responses)

    """