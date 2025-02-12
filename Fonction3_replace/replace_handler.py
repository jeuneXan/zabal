from solver.preparer_donnees import preparer_donnees_optimisation
from solver.optimiser import optimiser_affectation_poseurs

if __name__ == "__main__":
    # Étape 1 : Préparer les données
    poseurs_libres, candidats = preparer_donnees_optimisation()

    # Étape 2 : Lancer l'optimisation
    optimiser_affectation_poseurs(poseurs_libres, candidats)
