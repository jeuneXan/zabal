from ortools.sat.python import cp_model
from datetime import datetime

def optimiser_affectation_poseurs(poseurs_libres, candidats):
    """Optimise l'affectation des poseurs via OR-Tools."""
    print("🚀 Début de l'optimisation avec OR-Tools")

    model = cp_model.CpModel()
    assignments = {}

    # Créer les variables de décision
    for poseur_info in poseurs_libres:
        poseur = poseur_info["poseur"]
        date_disponible = poseur_info["date_disponible"]
        candidats_possibles = [
            rdv for rdv in candidats
            if poseur in rdv["affectation_ressources"] and datetime.fromisoformat(rdv["date_debut"][:-1]).date() >= date_disponible
        ]
        
        for j, candidat in enumerate(candidats_possibles):
            assignments[(poseur, j)] = model.NewBoolVar(f"assign_{poseur}_{j}")

        model.Add(sum(assignments[(poseur, j)] for j in range(len(candidats_possibles))) <= 1)

    # Objectif : maximiser le nombre de remplacements
    print("Poseurs libres :", poseurs_libres)
    model.Maximize(sum(assignments[(poseur, j)] for poseur, j in assignments))

    # Résolution du modèle
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    resultats = []
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for poseur_info in poseurs_libres:
            poseur = poseur_info["poseur"]
            for j, candidat in enumerate(candidats):
                if solver.Value(assignments.get((poseur, j), 0)) == 1:
                    print(f"🔄 {candidat['nom']} ({candidat['id_rdv']}) remplace un annulé.")
                    resultats.append({
                        "poseur": poseur,
                        "remplacement": candidat['nom'],
                        "id_rdv": candidat['id_rdv']
                    })
    else:
        print("❌ Aucune solution trouvée.")

    return resultats  # Ajout du retour des résultats
