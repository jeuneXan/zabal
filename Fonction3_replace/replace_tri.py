from datetime import datetime
from solver.utils import charger_rendez_vous, jours_ouvres, distance_moyenne_avec_poseurs

def preparer_donnees_optimisation():
    """Charge et trie les rendez-vous avant optimisation."""
    print("✅ Préparation des données pour l'optimisation")

    today = datetime.today().date()
    jours_a_considerer = jours_ouvres(today, 4)
    rendez_vous = charger_rendez_vous()

    print(f"📂 {len(rendez_vous)} rendez-vous chargés !")

    # Identifier les derniers rendez-vous des poseurs
    dernier_rdv_poseur = {}
    for rdv in rendez_vous:
        for poseur in rdv["affectation_ressources"]:
            date_rdv = datetime.fromisoformat(rdv["date_debut"][:-1])
            if poseur not in dernier_rdv_poseur or date_rdv > dernier_rdv_poseur[poseur]["date_debut"]:
                dernier_rdv_poseur[poseur] = {
                    "coordonnees_gps": rdv["coordonnees_gps"],
                    "date_debut": date_rdv
                }

    # Identifier les rendez-vous annulés
    annulations = [
        rdv for rdv in rendez_vous
        if rdv["statut"] == "annulé" and datetime.fromisoformat(rdv["date_debut"][:-1]).date() in jours_a_considerer
    ]

    print(f"❌ {len(annulations)} rendez-vous annulés détectés !")

    # Extraire les poseurs devenus libres
    poseurs_libres = [
        {"poseur": poseur, "date_disponible": datetime.fromisoformat(annulation["date_debut"][:-1]).date()}
        for annulation in annulations
        for poseur in annulation["affectation_ressources"]
    ]

    print(f"📌 {len(poseurs_libres)} poseurs sont disponibles suite aux annulations.")

    # Trouver les candidats pour remplacement
    candidats_filtres = []
    for annulation in annulations:
        date_annulation = datetime.fromisoformat(annulation["date_debut"][:-1]).date()
        candidats_valides = [
            rdv for rdv in rendez_vous
            if rdv["statut"] == "proposé" and datetime.fromisoformat(rdv["date_debut"][:-1]).date() > date_annulation
        ]
        print(f"📌 {len(candidats_valides)} candidats valides pour remplacer {annulation['nom']} ({annulation['id_rdv']})")
        candidats_filtres.extend(candidats_valides)

    # Supprimer les doublons
    candidats = list({rdv["id_rdv"]: rdv for rdv in candidats_filtres}.values())

    # Trier les candidats par critères
    candidats.sort(
        key=lambda x: (
            distance_moyenne_avec_poseurs(x, dernier_rdv_poseur),
            (not x["marchandise"] or x["marchandise_livree"]),
            x["duree"],
            -len(x["affectation_ressources"])
        )
    )

    print(f"📌 {len(candidats)} candidats finaux après tri.")

    # Retourner les données triées
    return poseurs_libres, candidats
