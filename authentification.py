import os
import requests
import re

# Variable privée pour stocker la session unique
_session = None

def login_to_api():
    """
    Se connecte à l'API en récupérant d'abord le jeton CSRF.
     """
    api_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    login_url = f"{api_url}/login"
    print(f"📡 Connexion à l'API : {api_url}")

    # Création d'une session pour gérer les cookies
    session = requests.Session()

    # 1️⃣ Étape 1 : Récupérer la page de login pour extraire le token CSRF
    response = session.get(login_url)
    if response.status_code != 200:
        print(f"❌ Erreur en récupérant la page de login ({response.status_code})")
        return None

    # Extraire le jeton CSRF du HTML
    match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', response.text)
    if not match:
        print("🚨 Impossible de récupérer le jeton CSRF. Vérifiez si la page de login a changé.")
        return None

    csrf_token = match.group(1)

    # 2️⃣ Étape 2 : Faire la requête de login avec le jeton CSRF
    login_data = {
        '_username': os.environ.get("API_USERNAME", "erle@disc-chantier.com"),
        '_password': os.environ.get("API_PASSWORD", "elre123.lo"),
        '_remember_me': 'on',
        '_csrf_token': csrf_token  # Ajout du token CSRF
    }

    response = session.post(login_url, data=login_data, allow_redirects=False)

    # Vérification de la connexion
    if response.status_code in [302, 200]:  # 302 = redirection après connexion réussie
        print("✅ Connexion réussie !")
    else:
        print(f"❌ Erreur de connexion ({response.status_code}) : {response.text}")
        return None

    return session

def get_api_session():
    """
    Retourne l'objet session unique pour accéder à l'API.
    """
    global _session
    if _session is None:
        _session = login_to_api()
    return _session
