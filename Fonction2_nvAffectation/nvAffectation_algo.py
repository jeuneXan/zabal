from datetime import datetime
from utils import to_datetime, haversine_distance

def reaffecter_rdv(data):
    """
    Réaffecte les rendez-vous d'une personne absente en fonction de la criticité
    et renvoie la liste des rendez-vous modifiés.
    
    Paramètres
    ----------
    data : dict
        - data["liste_rdv"] : liste de dictionnaires représentant les RDV
        - data["personne_absente"] : identifiant de la personne absente
    
    Retour
    ------
    list
        liste de dictionnaires (rendez-vous) qui ont été modifiés durant le processus.
    """
    liste_rdv = data.get("sorted_data", [])
    personne_absente = data.get("employe_absent", None)

    
    # -- 2) Séparer les RDV absents (qui incluent la personne_absente) et les autres --
    rdv_absent = []
    rdv_autres = []
    print("list",liste_rdv)
    for rdv in liste_rdv:
        # Si la personne absente apparaît dans "affectation_ressources_defini"
        # => on considère ce RDV comme "rdv_absent"
        if personne_absente in rdv.get("affectation_ressources_defini", []):
            print("abs",rdv)
            rdv_absent.append(rdv)
        else:
            print("autre",rdv)
            rdv_autres.append(rdv)
    
    # -- Pour éviter de dupliquer dans la liste finale, on garde un set des ID modifiés --
    changed_rdvs = {}

    # Helper pour vérifier le chevauchement de dates
    def chevauchement(r1, r2):
        """
        Retourne True si r1 et r2 se chevauchent (au moins partiellement).
        """
        debut1, fin1 = r1["date_debut"], r1["date_fin"]
        debut2, fin2 = r2["date_debut"], r2["date_fin"]
        return (debut1 < fin2) and (debut2 < fin1)
    
    # Helper pour extraire lat, lon
    def get_lat_lon(rdv):
        lat_str, lon_str = rdv["coordonnees_gps"].split(",")
        return float(lat_str.strip()), float(lon_str.strip())
    
    # -- 3) Tenter de réaffecter chaque RDV absent --
    for rdv_a in rdv_absent:
        # On retire la ressource absente
        old_defini = rdv_a.get("affectation_ressources_defini", [])
        print("old_defini",old_defini)
        if personne_absente in old_defini:
            new_defini = [res for res in old_defini if res != personne_absente]
            rdv_a["affectation_ressources_defini"] = new_defini
        
        # Combien de ressources sont nécessaires ?
        ressources_needed = rdv_a.get("nombre_ressources", 1)
        
        # On va stocker ici les ressources qu'on parvient à assigner
        new_resources_assigned = []
        
        # On récupère la liste des ressources possibles
        possibles = rdv_a.get("affectation_ressources_possible", [])
        print("possibles",possibles)
        # Récupère la coordonnée GPS du RDV absent (pour distance)
        lat_a, lon_a = get_lat_lon(rdv_a)
        
        # Tentative d'assigner chaque ressource jusqu'à en avoir assez
        for _ in range(ressources_needed):
            # Construire la liste des ressources actuellement **disponibles** ou “volables”
            # On va évaluer chaque resource dans "possibles" qui n’est pas déjà choisie
            candidats = []
            
            for ressource in possibles:
                if ressource in new_resources_assigned:
                    # Ressource déjà prise pour ce RDV
                    continue
                
                # 1) Trouver quels RDV (dans rdv_autres) utilisent cette ressource
                #    ET qui ont un créneau qui chevauche
                rdv_en_conflit = []
                for autre in rdv_autres:
                    # Vérifions si la ressource est dans 'autre'
                    defini_autre = autre.get("affectation_ressources_defini", [])
                    if ressource in defini_autre:
                        # On teste le chevauchement strict
                        if chevauchement(rdv_a, autre):
                            rdv_en_conflit.append(autre)
                
                # 2) Vérifier si on peut “battre” tous les RDV en conflit 
                #    (i.e. criticité absente > criticité des autres).
                #    Si criticité égale ou inférieure => on ne peut pas récupérer cette ressource.
                can_take = True
                for c in rdv_en_conflit:
                    if rdv_a["criticite"] <= c["criticite"]:
                        # Si égalité ou inférieur => on ne vole pas
                        can_take = False
                        break
                
                if not can_take:
                    continue
                
                # 3) Si on peut la prendre, calculer la distance pour prioriser
                #    la ressource associée au RDV le “plus proche”. 
                #    On va prendre la distance minimale vis-à-vis de tous les RDV en conflit
                #    (ou 0 s’il n’y a pas de conflit du tout).
                if len(rdv_en_conflit) > 0:
                    min_distance = float('inf')
                    for c in rdv_en_conflit:
                        lat_c, lon_c = get_lat_lon(c)
                        dist = haversine_distance(lat_a, lon_a, lat_c, lon_c)
                        if dist < min_distance:
                            min_distance = dist
                else:
                    # Pas de conflit => distance nulle pour dire “très favorable”
                    min_distance = 0
                
                # On stocke ce candidat
                candidats.append((ressource, min_distance, rdv_en_conflit))
            
            if not candidats:
                # Aucune ressource n’est récupérable => on arrête
                break
            
            # Parmi tous les candidats, on prend celui dont la distance est la plus faible
            candidats.sort(key=lambda x: x[1])  # tri par distance
            best_ressource, best_dist, best_conflits = candidats[0]
            
            # On “vole” cette ressource (ou elle est libre)
            # => pour chaque RDV en conflit, on annule leurs ressources + date
            print("Best conflit",best_conflits)
            for victime in best_conflits:
                print("Grosse victime",victime)
                victime["date_debut"] = None
                victime["date_fin"] = None
                victime["affectation_ressources_defini"] = []
                victime["alerte"] = (
                    f"Rdv annulé car personne plus critique ({rdv_a['id_rdv']}) a récupéré la ressource."
                )
                changed_rdvs[victime["id_rdv"]] = victime
            
            # On ajoute cette ressource au RDV absent
            print("best",best_ressource)
            new_resources_assigned.append(best_ressource)
        
        # -- Fin de la boucle d’assignation pour ce RDV absent --
        if len(new_resources_assigned) == ressources_needed:
            # On a trouvé suffisamment de ressources
            rdv_a["affectation_ressources_defini"] = new_resources_assigned
            # On signale que ce RDV a été modifié
            changed_rdvs[rdv_a["id_rdv"]] = rdv_a
        else:
            # Échec => on annule ce RDV absent
            rdv_a["date_debut"] = None
            rdv_a["date_fin"] = None
            rdv_a["affectation_ressources_defini"] = []
            rdv_a["alerte"] = (
                f"Rdv annulé car pas de ressources disponibles pour remplacer l'absence de {personne_absente}"
            )
            changed_rdvs[rdv_a["id_rdv"]] = rdv_a
    
    # -- 4) Construire la liste des RDV modifiés à partir de changed_rdvs --
    liste_modifies = list(changed_rdvs.values())
    print("liste_modifies",liste_modifies)
    return liste_modifies
