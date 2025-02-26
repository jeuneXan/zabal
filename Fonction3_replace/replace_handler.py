import os
from datetime import datetime
from replace_tri import (
    preparer_donnees_remplacement,
    filtrer_phase1,
    filtrer_phase2,
    filtrer_phase2b,
    filtrer_phase2c
)
from replace_algo import optimiser_affectation_poseurs, optimiser_affectation_multi

def run_optimisation_remplacement(rdv_id: str):
    """
    Approche multi-phase :
      1) PHASE 1 : RDV unique (même durée, équipe identique).
      2) PHASE 2 : RDV unique (même durée, même nb poseurs, >=1 poseur commun).
      2.5) PHASE 2.5 : RDV unique (même durée, même nb poseurs, >=1 poseur dans recommandés).
      2.6) PHASE 2.6 : RDV unique (même durée, même nb poseurs, sans contrainte de composition).
      3) PHASE 3 : décomposition multi-rdv (même ou plus courte durée).
    """

    # Récupération de l'équipe annulée, la durée, etc.
    poseurs_libres, candidats, rdv_annule = preparer_donnees_remplacement(rdv_id)
    if not rdv_annule or not poseurs_libres:
        return {
            "message": f"Aucun remplacement possible (RDV {rdv_id} introuvable ou poseurs inexistants)",
            "affectations": []
        }

    # PHASE 1
    phase1_candidates = filtrer_phase1(rdv_annule, candidats)
    if phase1_candidates:
        result1 = optimiser_affectation_poseurs(
            poseurs_libres, phase1_candidates, rdv_annule, phase_name="PHASE 1"
        )
        if result1:
            return {"message": "Remplacement terminé (Phase 1)", "affectations": result1}

    # PHASE 2
    phase2_candidates = filtrer_phase2(rdv_annule, candidats)
    if phase2_candidates:
        result2 = optimiser_affectation_poseurs(
            poseurs_libres, phase2_candidates, rdv_annule, phase_name="PHASE 2"
        )
        if result2:
            return {"message": "Remplacement terminé (Phase 2)", "affectations": result2}

    # PHASE 2.5
    phase2b_candidates = filtrer_phase2b(rdv_annule, candidats)
    if phase2b_candidates:
        result2b = optimiser_affectation_poseurs(
            poseurs_libres, phase2b_candidates, rdv_annule, phase_name="PHASE 2.5"
        )
        if result2b:
            return {"message": "Remplacement terminé (Phase 2.5)", "affectations": result2b}

    # PHASE 2.6
    phase2c_candidates = filtrer_phase2c(rdv_annule, candidats)
    if phase2c_candidates:
        result2c = optimiser_affectation_poseurs(
            poseurs_libres, phase2c_candidates, rdv_annule, phase_name="PHASE 2.6"
        )
        if result2c:
            return {"message": "Remplacement terminé (Phase 2.6)", "affectations": result2c}

    # PHASE 3
    if len(poseurs_libres) > 1:
        result3 = optimiser_affectation_multi(poseurs_libres, candidats, rdv_annule)
        if result3:
            return {"message": "Remplacement terminé (Phase 3, multi-rdv)", "affectations": result3}

    return {
        "message": "Aucun remplacement possible (Toutes phases échouées)",
        "affectations": []
    }


if __name__ == "__main__":
    test_id = "12424"
    output = run_optimisation_remplacement(test_id)
    print(output)
