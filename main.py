import os
import requests
import uvicorn
from authentification import get_api_session


if __name__ == "__main__":
    # Connexion à l'API et enregistrement du cookie de session
    api_session = get_api_session()
    
    # Optionnel : si votre application FastAPI doit accéder à la session,
    # vous pouvez la stocker dans l'objet "state" de l'app (par exemple dans "api.py")
    # from api import app
    # app.state.api_session = api_session
    
    # Récupération des variables d'environnement pour l'hôte et le port avec valeurs par défaut
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    
    # Lancement de l'application avec uvicorn
    uvicorn.run("api:app", host=host, port=port, reload=True)

