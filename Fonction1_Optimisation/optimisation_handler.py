# optimisation_handler.py
from Fonction1_Optimisation.optimisationTournee_tri import optimisationTournee_tri
from Fonction1_Optimisation.optimisationTournee_algo import optimize_schedule
from Fonction1_Optimisation.optimisationTournee_majDISC import update_interventions

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
    nb_days = data.get("nbJours")
    print("avant opt",sorted_data)
    result = optimize_schedule(sorted_data, nb_days)
    print("apres opt",result)
    maj_DISC = update_interventions(result)
    return maj_DISC
