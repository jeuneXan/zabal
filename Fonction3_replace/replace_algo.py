from ortools.sat.python import cp_model
from datetime import datetime, timedelta

def get_bonus_for_marchandises(rdv_candidat):
        """
        Définit le bonus en fonction du statut des marchandises.
        Plus le RDV est prêt en termes de marchandises, plus le bonus est élevé.
        """
        marchandises = rdv_candidat.get("marchandises", [])
        
        if not marchandises:
            return 4  # ✅ 1️⃣ Pas de marchandises => priorité max
        
        statuts = {m["statusmarchandise"]["nom"] for m in marchandises if "statusmarchandise" in m}
        
        if statuts == {"Livré", "Posé"}:
            return 3  # ✅ 2️⃣ Toutes les marchandises sont "Livré" ou "Posé"
        
        if statuts <= {"Livré", "Posé", "Réceptionné"}:
            return 2  # ✅ 3️⃣ Toutes les marchandises sont "Livré", "Posé" ou "Réceptionné"
        
        # ✅ 4️⃣ Vérifier si toutes les dateARC sont au moins 1 jour avant le RDV annulé
        date_annulation = datetime.fromisoformat(rdv_candidat.get("daterv", "").split("+")[0]).date()
        all_before = all(
            "dateARC" in m and datetime.fromisoformat(m["dateARC"].split("+")[0]).date() <= date_annulation - timedelta(days=1)
            for m in marchandises
        )

        if all_before:
            return 1  # ✅ Bonus faible si toutes les marchandises sont prêtes la veille

        return 0  # Pas de bonus sinon

def optimiser_affectation_poseurs(poseurs_libres, candidats, rdv_annule, phase_name="PhaseX"):
    """
    OR-Tools : un poseur = au plus un RDV.
    Priorité aux RDV sans marchandise ou avec des statuts favorables.
    """
    model = cp_model.CpModel()
    assignments = {}

    for poseur_info in poseurs_libres:
        poseur = poseur_info["poseur"]
        date_dispo = poseur_info["date_disponible"]

        candidats_possibles = []
        for j, rdv in enumerate(candidats):
            dt_str = rdv.get("daterv", "")
            if dt_str:
                dt_rdv = datetime.fromisoformat(dt_str.split("+")[0]).date()
                if dt_rdv >= date_dispo:
                    candidats_possibles.append((j, rdv))

        for (j, _) in candidats_possibles:
            assignments[(poseur, j)] = model.NewBoolVar(f"assign_{poseur}_{j}")

        if candidats_possibles:
            model.Add(sum(assignments[(poseur, j)] for (j, _) in candidats_possibles) <= 1)

    # -------------------
    # Définir l’objectif
    # -------------------

    objective_expr = []
    for (poseur, j) in assignments:
        base_value = 1
        bonus = get_bonus_for_marchandises(candidats[j])
        objective_expr.append(assignments[(poseur, j)] * (base_value + bonus))

    model.Maximize(sum(objective_expr))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    resultats = []
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for (poseur, j) in assignments:
            if solver.Value(assignments[(poseur, j)]) == 1:
                rdv_nouveau = candidats[j]
                date_heure = rdv_nouveau.get("daterv", "")
                adresse = rdv_nouveau.get("chantier", {}).get("adresse", "")
                resultats.append({
                    "poseur": poseur,
                    "nouveau_rdv": {
                        "id": rdv_nouveau["id"],
                        "date_heure": date_heure,
                        "adresse": adresse,
                        "duree": rdv_nouveau.get("duree", "?")
                    },
                    "ancien_rdv": {
                        "id": rdv_annule["id"],
                        "date_heure": rdv_annule.get("daterv", ""),
                        "duree": rdv_annule.get("duree", ""),
                        "etat": "désormais sans date"
                    },
                    "phase": phase_name
                })
    return resultats


def optimiser_affectation_multi(poseurs_libres, candidats, rdv_annule):
    """
    PHASE 3 : 
    - Chaque poseur peut être affecté à plusieurs RDV, 
      tant que la somme des durées n’excède pas la durée du RDV annulé.
    - On favorise les RDV avec des statuts favorables pour les marchandises.
    """
    try:
        duree_annule = int(float(rdv_annule.get("duree", "1")))  # 🔧 Conversion robuste
    except ValueError:
        duree_annule = 1

    model = cp_model.CpModel()
    assignments = {}
    rdv_durations = {}

    for i, c in enumerate(candidats):
        try:
            rdv_durations[i] = int(float(c.get("duree", "1")))  # 🔧 Conversion robuste
        except ValueError:
            rdv_durations[i] = 1

    for poseur_info in poseurs_libres:
        poseur = poseur_info["poseur"]
        for j in range(len(candidats)):
            assignments[(poseur, j)] = model.NewBoolVar(f"assign_{poseur}_{j}")

    for poseur_info in poseurs_libres:
        poseur = poseur_info["poseur"]
        model.Add(
            sum(assignments[(poseur, j)] * int(rdv_durations[j]) for j in range(len(candidats))) 
            <= int(duree_annule)
        )

    def get_bonus(poseur, rdv_candidat):
        users_c = [u["username"] for u in rdv_candidat.get("users", [])]
        recommended_c = [u["username"] for u in rdv_candidat.get("users_recommended", [])]
        marchandises_bonus = get_bonus_for_marchandises(rdv_candidat)

        if poseur in users_c or poseur in recommended_c:
            return 2 + marchandises_bonus
        return 1 + marchandises_bonus

    objective_expr = []
    for (poseur, j) in assignments:
        bonus = get_bonus(poseur, candidats[j])
        objective_expr.append(assignments[(poseur, j)] * bonus)

    model.Maximize(sum(objective_expr))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    resultats = []
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for (poseur, j) in assignments:
            if solver.Value(assignments[(poseur, j)]) == 1:
                rdv_nouveau = candidats[j]
                date_heure = rdv_nouveau["daterv"]
                adresse = rdv_nouveau.get("chantier", {}).get("adresse", "")
                resultats.append({
                    "poseur": poseur,
                    "nouveau_rdv": {
                        "id": rdv_nouveau["id"],
                        "date_heure": date_heure,
                        "adresse": adresse,
                        "duree": rdv_nouveau.get("duree", "?")
                    },
                    "ancien_rdv": {
                        "id": rdv_annule["id"],
                        "date_heure": rdv_annule.get("daterv", ""),
                        "duree": rdv_annule.get("duree", ""),
                        "etat": "désormais sans date"
                    },
                    "phase": "PHASE 3 multi"
                })

    return resultats
