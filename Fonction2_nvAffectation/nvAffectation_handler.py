# optimisation_handler.py
from Fonction2_nvAffectation.nvAffectation_tri import nvAffectation_tri
from Fonction2_nvAffectation.nvAffectation_algo import reaffecter_rdv

def run_nvAffectation(data):
    """
    Réalise l'optimisation en deux étapes :
      1. Trie les informations via la fonction `optimisationTournee_tri` (définie dans optimisationTournee_tr.py).
      2. Utilise le résultat du tri en tant que paramètre pour `optimisationTournee_algo` (définie dans optimisationTournee_algo.py).
    
    :param data: Les données d'entrée (par exemple, un dictionnaire contenant les informations nécessaires).
    :return: Le résultat final de l'optimisation.
    """
    # Étape 1 : Tri des données
    print("lancement tri")
    sorted_data = nvAffectation_tri(data)
    # Étape 2 : Application de l'algorithme d'optimisation sur les données triées
    employe_absent = data.get("employeAbsent")
    print("employe", employe_absent)
    data_for_algo = {
        "sorted_data": sorted_data,
        "employe_absent": int(employe_absent)
    }
    print("lancement algo", data_for_algo)
    result = reaffecter_rdv(data_for_algo)
    
    return result
