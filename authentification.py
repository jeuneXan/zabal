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
      - API_REMEMBERME : Valeur à forcer pour le cookie REMEMBERME (si nécessaire)
    """
    # Récupération de l'URL de base
    api_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    login_url = f"{api_url}/login"
    print(f"Connexion à l'API : {api_url}")

    # Préparation des données de connexion, en incluant le paramètre _remember_me
    login_data = {
        '_username': os.environ.get("API_USERNAME", "erle@disc-chantier.com"),
        '_password': os.environ.get("API_PASSWORD", "elre123.lo"),
        '_csrf_token': os.environ.get("API_CSRF_TOKEN", ""),
        '_remember_me': 'on'  # Envoi du paramètre pour activer le "remember me"
    }

    # Ajout d'en-têtes pour imiter le comportement d'un navigateur
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Referer": f"{api_url}/login",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    # Création d'une session qui gère automatiquement les cookies
    session = requests.Session()

    # Envoi de la requête de connexion (les redirections sont suivies par défaut)
    response = session.post(login_url, data=login_data, headers=headers)

    if response.ok:
        print("Connexion réussie à l'API.")
    else:
        print("Erreur lors de la connexion à l'API :", response.status_code)
        print("Détails :", response.text)

    # Affichage des cookies récupérés initialement
    cookies = session.cookies.get_dict()
    print("Cookies récupérés initialement :", cookies)

    # Si le cookie REMEMBERME n'est pas présent, le forcer
    if 'REMEMBERME' not in cookies:
        # Récupère une valeur par défaut depuis l'environnement ou utilise une valeur "forcée"
        remember_me_value = os.environ.get("API_REMEMBERME", "App.Entity.User%3AZXJsZUBkaXNjLWNoYW50aWVyLmNvbQ~~%3A1739978022%3Adn0fdCzTUkDuoIdedZvKQteSBNcSHmnyCEs72A-lnE4~YAMrK0_6zOipEX14AKgDe3rIV0tkIjqWapbTPYlwB-k~")
        # Force l'ajout du cookie REMEMBERME dans la session
        session.cookies.set("REMEMBERME", remember_me_value,
                              domain="preprod.disc-chantier.com",
                              path="/")
        print("Cookie REMEMBERME forcé dans la session.")

    # Affichage final des cookies
    final_cookies = session.cookies.get_dict()
    print("Cookies finaux dans la session :", final_cookies)

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
