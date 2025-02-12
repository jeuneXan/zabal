import os
from datetime import datetime
from replace_tri import preparer_donnees_optimisation
from replace_algo import optimiser_affectation_poseurs

def run_optimisation_A(employe: str = None, date_debut: str = None, date_fin: str = None):
    """
    Exécute l'optimisation des poseurs.
    
    Paramètres :
      - employe (str) : Nom de l'employé concerné (optionnel)
      - date_debut (str) : Date de début de la période à optimiser (format ISO)
      - date_fin (str) : Date de fin de la période à optimiser (format ISO)
    
    Retourne :
      - Une liste des affectations optimisées.
    """
    print("🚀 Lancement de l'optimisation des affectations de poseurs")

    # Étape 1 : Charger et filtrer les données
    poseurs_libres, candidats = preparer_donnees_optimisation()
    
    if not poseurs_libres or not candidats:
        print("⚠️ Aucune donnée à optimiser")
        return {"message": "Aucune donnée à optimiser", "affectations": []}

    # Étape 2 : Filtrer selon les paramètres API (si fournis)
    if employe:
        poseurs_libres = [p for p in poseurs_libres if p["poseur"] == employe]
    if date_debut:
        date_debut = datetime.fromisoformat(date_debut)
        candidats = [c for c in candidats if datetime.fromisoformat(c["date_debut"][:-1]) >= date_debut]
    if date_fin:
        date_fin = datetime.fromisoformat(date_fin)
        candidats = [c for c in candidats if datetime.fromisoformat(c["date_fin"][:-1]) <= date_fin]

    # Étape 3 : Lancer l’optimisation
    resultats = optimiser_affectation_poseurs(poseurs_libres, candidats)

    return {
        "message": "Optimisation terminée",
        "affectations": resultats
    }

if __name__ == "__main__":
    # Simulation d'un jeu de données statique pour tester la fonction A
    print("🔬 Test local de la fonction A avec des données statiques...")

    # Appel de l'optimisation sans filtre spécifique
    result = run_optimisation_A()
    
    print("✅ Résultats de l'optimisation :")
    print(result)
