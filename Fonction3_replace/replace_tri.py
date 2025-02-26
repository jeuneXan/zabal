from datetime import datetime, timedelta
from replace_utils import charger_rendez_vous

def preparer_donnees_remplacement(rdv_id: str):
    """
    Récupère tous les RDV,
    Trouve le RDV annulé (rdv_id),
    Extrait la date, la durée, et l'équipe.
    Construit la liste (poseurs_libres, candidats).
    
    Renvoie :
      - poseurs_libres : [{"poseur": name, "date_disponible": date_annulation}, ...]
      - candidats : tous les RDV potentiels dans les 7 jours
      - rdv_annule : le RDV annulé lui-même
    """
    print(f"Préparation des données pour le RDV annulé {rdv_id}")

    all_rdv = charger_rendez_vous()
    if not all_rdv:
        print("Aucun RDV récupéré depuis la source.")
        return [], [], None

    rdv_annule = None
    for jour_data in all_rdv:
        for rdv in jour_data.get("rvs", []):
            if str(rdv.get("id")) == rdv_id:
                rdv_annule = rdv
                break
        if rdv_annule:
            break

    if not rdv_annule:
        print(f"RDV {rdv_id} introuvable dans les données.")
        return [], [], None

    # Affiche rapidement le RDV annulé
    print("RDV annulé :", rdv_annule)

    # Extraire la date d'annulation
    daterv_str = rdv_annule.get("daterv", "")
    if not daterv_str:
        return [], [], None
    date_annulation = datetime.fromisoformat(daterv_str.split("+")[0]).date()

    # Gérer la durée
    duree_annule = rdv_annule.get("duree", "")
    if not duree_annule:
        duree_annule = "1"

    # Récupérer les poseurs
    poseurs_concernes = [u["username"] for u in rdv_annule.get("users", [])]

    # Si tous sont "À planifier", on ne fait rien
    if all(p == "À planifier" for p in poseurs_concernes):
        print("Tous les poseurs sont 'À planifier', aucune optimisation à faire.")
        return [], [], None

    poseurs_libres = [
        {"poseur": p, "date_disponible": date_annulation} 
        for p in poseurs_concernes
    ]

    # Construire la liste des RDV candidats (dans les 7 jours)
    date_limite = date_annulation + timedelta(days=7)
    candidats_filtres = []
    for jour_data in all_rdv:
        for rdv in jour_data.get("rvs", []):
            if str(rdv.get("id")) == str(rdv_annule["id"]):
                continue
            dt_str = rdv.get("daterv", "")
            if not dt_str:
                continue
            dt_rdv = datetime.fromisoformat(dt_str.split("+")[0]).date()
            if date_annulation <= dt_rdv <= date_limite:
                candidats_filtres.append(rdv)

    print(f"{len(candidats_filtres)} RDV candidats dans la fenêtre de 7 jours.")
    return poseurs_libres, candidats_filtres, rdv_annule


# ------------------------------
# Fonctions de filtrage par phase
# ------------------------------

def filtrer_phase1(rdv_annule, candidats):
    """
    PHASE 1 : même durée, même équipe.
    """
    duree_annule = rdv_annule.get("duree", "1")
    users_annule = {u["username"] for u in rdv_annule.get("users", [])}
    
    phase1 = []
    for c in candidats:
        if c.get("duree") == duree_annule:
            users_c = {u["username"] for u in c.get("users", [])}
            if users_c == users_annule:
                phase1.append(c)
    return phase1


def filtrer_phase2(rdv_annule, candidats):
    """
    PHASE 2 : même durée, même nb poseurs, >=1 poseur en commun.
    """
    duree_annule = rdv_annule.get("duree", "1")
    users_annule = [u["username"] for u in rdv_annule.get("users", [])]
    nb_annule = len(users_annule)
    set_annule = set(users_annule)

    phase2 = []
    for c in candidats:
        if c.get("duree") == duree_annule:
            users_c = [u["username"] for u in c.get("users", [])]
            if len(users_c) == nb_annule:
                set_c = set(users_c)
                if set_annule & set_c:  # intersection
                    phase2.append(c)
    return phase2


def filtrer_phase2b(rdv_annule, candidats):
    """
    PHASE 2.5 : même durée, même nb poseurs, >=1 poseur dans 'users_recommended'.
    """
    duree_annule = rdv_annule.get("duree", "1")
    users_annule = [u["username"] for u in rdv_annule.get("users", [])]
    nb_annule = len(users_annule)
    set_annule = set(users_annule)

    phase2b = []
    for c in candidats:
        if c.get("duree") == duree_annule:
            users_c = [u["username"] for u in c.get("users", [])]
            if len(users_c) == nb_annule:
                recommended_c = [u for u in c.get("users_recommended", [])]
                recommended_names = set(u["username"] for u in recommended_c)
                if set_annule & recommended_names:
                    phase2b.append(c)
    return phase2b


def filtrer_phase2c(rdv_annule, candidats):
    """
    PHASE 2.6 : même durée, même nb poseurs, pas de contrainte de commun.
    """
    duree_annule = rdv_annule.get("duree", "1")
    users_annule = rdv_annule.get("users", [])
    nb_annule = len(users_annule)

    phase2c = []
    for c in candidats:
        if c.get("duree") == duree_annule:
            users_c = c.get("users", [])
            if len(users_c) == nb_annule:
                phase2c.append(c)
    return phase2c


def filtrer_phase3(rdv_annule, candidats):
    """
    PHASE 3 : ex. autoriser durée <= duree_annule (non implémenté ici).
    """
    return candidats
