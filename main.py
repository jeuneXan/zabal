import os
import requests
import uvicorn

def login_to_api():
    """
    Se connecte à l'API en utilisant les variables d'environnement et enregistre le cookie de session.
    
    Variables d'environnement utilisées (avec valeurs par défaut) :
      - API_URL : URL de base de l'API (défaut : "https://preprod.disc-chantier.com")
      - API_USERNAME : Nom d'utilisateur pour la connexion (défaut : "erle@disc-chantier.com")
      - API_PASSWORD : Mot de passe pour la connexion (défaut : "elre123.lo")
      - API_CSRF_TOKEN : Jeton CSRF si nécessaire (défaut : chaîne vide)
    """
    # Récupération de l'URL de base de l'API depuis l'environnement (ou valeur par défaut)
    api_url = os.environ.get("API_URL", "https://preprod.disc-chantier.com")
    # Construction de l'URL de connexion
    login_url = f"{api_url}/login"
    print(f"Connexion à l'API : {api_url}")
    
    # Préparation des données de connexion avec valeurs par défaut
    login_data = {
        '_username': os.environ.get("API_USERNAME", "erle@disc-chantier.com"),
        '_password': os.environ.get("API_PASSWORD", "elre123.lo"),
        '_csrf_token': os.environ.get("API_CSRF_TOKEN", "")  # Valeur par défaut vide si non utilisée
    }
    
    # Création d'une session qui conservera automatiquement les cookies
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
    
    # Retourne l'objet session pour d'éventuels appels ultérieurs
    return session

if __name__ == "__main__":
    # Connexion à l'API et enregistrement du cookie de session
    api_session = login_to_api()
    
    # Optionnel : si votre application FastAPI doit accéder à la session,
    # vous pouvez la stocker dans l'objet "state" de l'app (par exemple dans "api.py")
    # from api import app
    # app.state.api_session = api_session
    
    # Récupération des variables d'environnement pour l'hôte et le port avec valeurs par défaut
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    
    # Lancement de l'application avec uvicorn
    uvicorn.run("api:app", host=host, port=port, reload=True)

