import os
import requests

# Variable privée pour stocker la session unique
_session = None

def login_to_api():
    """
    Se connecte à l'API en utilisant les variables d'environnement et enregistre le cookie de session.
    
    Variables d'environnement (avec valeurs par défaut) :
      - API_URL : URL de base de l'API (défaut : "https://preprod.disc-chantier.com")
      - API_USERNAME : Nom d'utilisateur (défaut : "erle@disc-chantier.com")
      - API_PASSWORD : Mot de passe (défaut : "elre123.lo")
      - API_CSRF_TOKEN : Jeton CSRF (défaut : chaîne vide)
    """
    # Récupération de l'URL de base de l'API (ou valeur par défaut)
    api_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    # Construction de l'URL de connexion
    login_url = f"{api_url}/login"
    print(f"Connexion à l'API : {api_url}")

    # Préparation des données de connexion
    login_data = {
        '_username': os.environ.get("API_USERNAME", "erle@disc-chantier.com"),
        '_password': os.environ.get("API_PASSWORD", "elre123.lo"),
        '_csrf_token': os.environ.get("API_CSRF_TOKEN", "")
    }

    # Création d'une session qui gère automatiquement les cookies
    session = requests.Session()

    # Envoi de la requête de connexion
    response = session.post(login_url, data=login_data)

    if response.ok:
        print("Connexion réussie à l'API.")
    else:
        print("Erreur lors de la connexion à l'API :", response.status_code)
        print("Détails :", response.text)

    # Affichage des cookies récupérés (dont le cookie de session)
    cookies = session.cookies.get_dict()
    print("Cookies récupérés :", cookies)

    return session

def get_api_session():
    """
    Retourne l'objet session unique pour accéder à l'API.
    La première fois, cela déclenche la connexion. Les appels suivants retournent la même session.
    """
    global _session
    if _session is None:
        _session = login_to_api()
    return _session
