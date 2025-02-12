# optimisation_handler.py
from optimisationTournee_tri import optimisationTournee_tri
from optimisationTournee_algo import optimize_schedule

def run_optimisation(data):
    """
    Réalise l'optimisation en deux étapes :
      1. Trie les informations via la fonction `optimisationTournee_tri` (définie dans optimisationTournee_tr.py).
      2. Utilise le résultat du tri en tant que paramètre pour `optimisationTournee_algo` (définie dans optimisationTournee_algo.py).
    
    :param data: Les données d'entrée (par exemple, un dictionnaire contenant les informations nécessaires).
    :return: Le résultat final de l'optimisation.
    """
    # Étape 1 : Tri des données
    print("lancement tri")
    sorted_data = optimisationTournee_tri(data)
    
    # Étape 2 : Application de l'algorithme d'optimisation sur les données triées
    print("lancement optimize")
    result = optimize_schedule(sorted_data)
    
    print(result)
    return result
