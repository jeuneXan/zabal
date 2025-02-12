#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script complet d’optimisation de planning avec OR‑Tools

Ce script prend en entrée une liste de rendez‑vous (au format JSON ou dictionnaires)
et un nombre de jours sur lesquels optimiser le planning.
Les rendez‑vous sont optimisés par jour et par période (matin : 8h-12h, après‑midi : 14h-17h),
en respectant les fenêtres temporelles et la contrainte de ressources.
Les rendez‑vous modifiables verront leur créneau (date_debut, date_fin) et leur affectation
(modification du champ affectation_ressources) mis à jour.
Seuls les rendez‑vous modifiés sont renvoyés en sortie.
"""

import math
import json
from datetime import datetime, date, timedelta
from collections import defaultdict
from copy import deepcopy

# Import OR-Tools
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# --------------------------
# CONSTANTES ET PARAMÈTRES
# --------------------------
# Plages horaires en minutes depuis minuit (heure locale)
MORNING_START = 8 * 60      # 8h00 = 480
MORNING_END   = 12 * 60     # 12h00 = 720
AFTERNOON_START = 14 * 60   # 14h00 = 840
AFTERNOON_END   = 17 * 60   # 17h00 = 1020

# Définition du dépôt (point de départ et d’arrivée des véhicules)
DEPOT_COORDINATES = (48.8566, 2.3522)  # Paris centre

# Pénalité pour ne pas visiter un rendez‑vous (à ajuster)
SKIP_PENALTY = 10000

# Durée de résolution maximale (secondes)
TIME_LIMIT = 10

# Tolérance pour synchronisation multi‑ressources (en minutes)
SYNC_TOLERANCE = 0  # ici, nous imposons l'égalité stricte

# --------------------------
# FONCTIONS UTILES
# --------------------------
def parse_gps(coord_str):
    """Convertit une chaîne 'lat, lon' en tuple de floats."""
    lat_str, lon_str = coord_str.split(',')
    return float(lat_str.strip()), float(lon_str.strip())

def haversine_distance(coord1, coord2):
    """Calcule la distance (en km) entre deux points (lat, lon) avec la formule de Haversine."""
    R = 6371  # Rayon de la Terre en km
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def travel_time(coord1, coord2, speed_kmh=50):
    """Calcule le temps de trajet (en minutes) entre deux points en utilisant une vitesse moyenne."""
    distance = haversine_distance(coord1, coord2)
    return int((distance / speed_kmh) * 60)

def time_to_minutes(dt_obj):
    """Convertit une datetime en minutes depuis minuit."""
    return dt_obj.hour * 60 + dt_obj.minute

def minutes_to_time_str(day_date, minutes_from_midnight):
    """Convertit un nombre de minutes depuis minuit en une chaîne ISO (sur la date donnée)."""
    hrs = minutes_from_midnight // 60
    mins = minutes_from_midnight % 60
    scheduled = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=hrs, minutes=mins)
    return scheduled.strftime("%Y-%m-%dT%H:%M:%SZ")

# --------------------------
# OPTIMISATION D'UNE PÉRIODE (matin ou après‑midi)
# --------------------------
def optimize_period_routing(appointments, day_date, period_start, period_end, vehicles):
    """
    Optimise une liste de rendez‑vous pour une période donnée (période = [period_start, period_end] en minutes depuis minuit)
    sur une journée donnée (day_date, objet datetime.date).
    vehicles : liste de noms d'employés (chaque véhicule correspond à un employé)
    
    Retourne un dictionnaire:
      { appointment_id: { "scheduled_start": minutes_from_midnight absolu,
                           "assigned_resources": [list of employee names] } }
    pour les rendez‑vous planifiés dans cette période.
    Seuls les rendez‑vous entièrement planifiés (toutes copies visitées) sont retournés.
    """
    period_duration = period_end - period_start
    # Structure pour stocker les nœuds du modèle.
    # Chaque nœud sera un dictionnaire contenant :
    #  - coord: tuple (lat, lon)
    #  - service_time: durée du rendez‑vous (en minutes)
    #  - time_window: (lower, upper) en minutes relatifs au début de la période (0 = period_start)
    #  - allowed_vehicles: liste d'indices (dans 'vehicles') autorisés pour ce rendez‑vous
    #  - appointment_id: id du rendez‑vous (pour retrouver l'information après résolution)
    #  - copy_index: numéro de copie (pour rendez‑vous multi‑ressources)
    nodes = []
    node_metadata = {}  # mapping: global_node_index -> (appointment_id, copy_index)
    
    # Commencer par le dépôt en position 0
    depot_node = {
        "coord": DEPOT_COORDINATES,
        "service_time": 0,
        "time_window": (0, period_duration),
        "allowed_vehicles": list(range(len(vehicles))),
        "appointment_id": None,
        "copy_index": None,
        "is_depot": True
    }
    nodes.append(depot_node)
    # Les groupes pour rendez‑vous multi‑ressources (appointment_id -> liste d'indices de nœuds)
    multi_resource_groups = defaultdict(list)
    
    # Pour chaque rendez‑vous de la liste
    for rdv in appointments:
        # Pour chaque rendez‑vous, nous considérons la durée et la fenêtre de disponibilité.
        # On suppose que les rendez‑vous modifiables disposent d'un intervalle [date_debut, date_fin] souhaité.
        try:
            rdv_start_dt = datetime.strptime(rdv["date_debut"], "%Y-%m-%dT%H:%M:%SZ")
            rdv_end_dt   = datetime.strptime(rdv["date_fin"], "%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            print(f"Erreur lors du parsing des dates pour rdv id {rdv['id_rdv']}: {e}")
            continue
        
        # Vérifier que le rendez‑vous concerne bien la journée en cours
        if rdv_start_dt.date() != day_date:
            continue  # On ne traite que les rendez‑vous de cette journée
        
        # Calculer la fenêtre souhaitée en minutes depuis minuit
        desired_lower = time_to_minutes(rdv_start_dt)
        desired_upper = time_to_minutes(rdv_end_dt)
        
        # Pour la période, on doit prendre l'intersection entre la fenêtre souhaitée et [period_start, period_end]
        lower_bound = max(desired_lower, period_start)
        upper_bound = min(desired_upper, period_end)
        if lower_bound > upper_bound:
            # Le rendez‑vous ne peut pas être programmé dans cette période
            continue
        
        # Pour un rendez‑vous non modifiable, on force une fenêtre très étroite (fixe)
        if rdv["modifiable"] == 0:
            tw_lower = lower_bound - period_start
            tw_upper = tw_lower + 1  # fenêtre d'une minute pour fixer le créneau
        else:
            tw_lower = lower_bound - period_start
            tw_upper = upper_bound - period_start

        # Récupérer la durée du rendez‑vous (en minutes)
        service_time = rdv["duree"]
        
        # Pour les coordonnées
        try:
            coord = parse_gps(rdv["coordonnees_gps"])
        except Exception as e:
            print(f"Erreur lors du parsing des coordonnées pour rdv id {rdv['id_rdv']}: {e}")
            continue
        
        # Déterminer les véhicules autorisés pour ce rendez‑vous
        # Pour un rendez‑vous modifiable, on prend la liste donnée
        # Pour un rendez‑vous non modifiable, on considère que la ressource est fixée (la première valeur de affectation_ressources)
        if rdv["modifiable"] == 0:
            allowed = [rdv["affectation_ressources"][0]]  # on force l'unique ressource
        else:
            allowed = rdv["affectation_ressources"]
        # Convertir ces noms en indices selon la liste globale 'vehicles'
        allowed_vehicle_indices = [i for i, emp in enumerate(vehicles) if emp in allowed]
        if not allowed_vehicle_indices:
            # Aucun véhicule disponible pour ce rendez‑vous
            continue
        
        # Nombre de copies à créer selon le nombre de ressources requises
        nb_copies = rdv.get("nombre_ressources", 1)
        for copy in range(nb_copies):
            node = {
                "coord": coord,
                "service_time": service_time,
                "time_window": (tw_lower, tw_upper),
                "allowed_vehicles": allowed_vehicle_indices,
                "appointment_id": rdv["id_rdv"],
                "copy_index": copy,
                "is_depot": False
            }
            node_index = len(nodes)
            nodes.append(node)
            node_metadata[node_index] = (rdv["id_rdv"], copy)
            # Si rendez‑vous multi‑ressources, regrouper les indices
            if nb_copies > 1:
                multi_resource_groups[rdv["id_rdv"]].append(node_index)
    
    # S'il n'y a aucun rendez‑vous à traiter dans cette période, on renvoie un résultat vide
    if len(nodes) <= 1:
        return {}
    
    # Construction de la matrice de temps entre tous les nœuds
    num_nodes = len(nodes)
    time_matrix = [[0] * num_nodes for _ in range(num_nodes)]
    # Pour chaque paire de nœuds, on calcule le temps de trajet (en minutes)
    for i in range(num_nodes):
        for j in range(num_nodes):
            coord_i = nodes[i]["coord"] if not nodes[i].get("is_depot", False) else DEPOT_COORDINATES
            coord_j = nodes[j]["coord"] if not nodes[j].get("is_depot", False) else DEPOT_COORDINATES
            time_matrix[i][j] = travel_time(coord_i, coord_j)
    
    # Préparer le data_model pour OR-Tools
    data = {}
    data['time_matrix'] = time_matrix
    # Pour chaque nœud, on enregistre la durée de service
    data['service_times'] = [node["service_time"] for node in nodes]
    # Fenêtres de temps pour chaque nœud (déjà calculées, en minutes relatifs à 0)
    data['time_windows'] = [node["time_window"] for node in nodes]
    data['allowed_vehicles'] = [node["allowed_vehicles"] for node in nodes]
    data['num_vehicles'] = len(vehicles)
    data['depot'] = 0
    
    # -------------------------------
    # Création du modèle Routing OR-Tools
    # -------------------------------
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)
    
    # Callback de coût : inclut le temps de trajet + durée de service.
    # Ce callback est utilisé pour l'objectif (minimiser le trajet total).
    def cost_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node   = manager.IndexToNode(to_index)
        service = data['service_times'][from_node] if from_node != data['depot'] else 0
        return data['time_matrix'][from_node][to_node] + service
    cost_callback_index = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(cost_callback_index)
    
    # Callback pour la dimension "Time" : n'ajoute que la durée du rendez‑vous,
    # le temps de trajet est ignoré pour permettre des rendez‑vous consécutifs.
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        service = data['service_times'][from_node] if from_node != data['depot'] else 0
        return service
    time_callback_index = routing.RegisterTransitCallback(time_callback)
    
    # Ajout de la dimension "Time"
    routing.AddDimension(
        time_callback_index,
        30,  # slack (attente maximale)
        period_duration,  # capacité maximale (la durée de la période)
        False,  # cumul ne commence pas à 0 automatiquement
        "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    
    # Appliquer les fenêtres de temps pour chaque nœud
    for node_index in range(len(data['time_windows'])):
        index = manager.NodeToIndex(node_index)
        window = data['time_windows'][node_index]
        time_dimension.CumulVar(index).SetRange(window[0], window[1])
    
    # Pour chaque rendez‑vous (non dépôt), restreindre les véhicules autorisés
    for node_index in range(1, len(nodes)):
        index = manager.NodeToIndex(node_index)
        allowed = data['allowed_vehicles'][node_index]
        routing.SetAllowedVehiclesForIndex(allowed, index)
    
    # Pour les rendez‑vous multi‑ressources, ajouter une contrainte de synchronisation
    # (on force l'égalité des variables temps entre les copies du même rendez‑vous)
    for rdv_id, node_indices in multi_resource_groups.items():
        if len(node_indices) < 2:
            continue
        # Pour chaque paire dans le groupe, imposer l'égalité des variables de temps
        for i in range(len(node_indices) - 1):
            idx1 = manager.NodeToIndex(node_indices[i])
            idx2 = manager.NodeToIndex(node_indices[i+1])
            routing.solver().Add(time_dimension.CumulVar(idx1) == time_dimension.CumulVar(idx2))
    
    # Pour favoriser la visite des rendez‑vous, ajouter des disjonctions avec pénalité
    for node_index in range(1, len(nodes)):
        routing.AddDisjunction([manager.NodeToIndex(node_index)], SKIP_PENALTY)
    
    # Paramètres de recherche
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.FromSeconds(TIME_LIMIT)
    
    # Résolution
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        print(f"Aucune solution trouvée pour la période {period_start}-{period_end} le {day_date}")
        return {}
    
    # Extraction des résultats
    # Pour chaque véhicule, récupérer la séquence de nœuds visités
    result = defaultdict(lambda: {"scheduled_start": None, "assigned_resources": []})
    visited_nodes = set()
    for veh in range(data['num_vehicles']):
        index = routing.Start(veh)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != data['depot']:
                visited_nodes.add(node)
                # On récupère l'heure programmée pour ce nœud
                t_var = time_dimension.CumulVar(index)
                scheduled_relative = solution.Value(t_var)
                scheduled_absolute = period_start + scheduled_relative  # minutes depuis minuit
                # Identifier le rendez‑vous correspondant
                rdv_id, copy_index = node_metadata[node]
                # Enregistrer la ressource (véhicule) affectée à ce nœud
                result[rdv_id]["assigned_resources"].append(vehicles[veh])
                # On enregistre l'heure de début (pour tous les duplicata, elles devraient être égales)
                result[rdv_id]["scheduled_start"] = scheduled_absolute
            index = solution.Value(routing.NextVar(index))
    
    # Pour les rendez‑vous multi‑ressources, s'assurer que toutes les copies ont été visitées
    # On parcourt les groupes et, si certaines copies sont manquantes, on supprime le rendez‑vous du résultat.
    for rdv_id, node_indices in multi_resource_groups.items():
        all_visited = all(n in visited_nodes for n in node_indices)
        if not all_visited:
            if rdv_id in result:
                del result[rdv_id]
    
    # Pour les rendez‑vous simples, vérifier qu'ils ont bien été visités
    # (Les rendez‑vous non visités ne figurent pas dans 'result')
    
    return result

# --------------------------
# OPTIMISATION SUR LA HORIZON (PLUSIEURS JOURS)
# --------------------------
def optimize_schedule(appointments, nb_days):
    """
    Optimise le planning sur nb_days jours (du jour courant jusqu'à aujourd'hui + nb_days),
    en considérant uniquement les jours travaillés (lundi à vendredi).
    
    appointments : liste de dictionnaires correspondant aux rendez‑vous
    Retourne une liste (de dictionnaires JSON) contenant uniquement les rendez‑vous modifiés,
    avec mise à jour des champs "date_debut", "date_fin" et "affectation_ressources".
    """
    # Pour les affectations, construire la liste globale des employés (véhicules)
    vehicles_set = set()
    for rdv in appointments:
        for emp in rdv["affectation_ressources"]:
            vehicles_set.add(emp)
    vehicles = sorted(list(vehicles_set))
    
    # Copier les rendez‑vous pour pouvoir les modifier sans altérer l'original
    appointments_mod = deepcopy(appointments)
    # Dictionnaire pour retrouver les rendez‑vous modifiés par id
    updated_rdvs = {}
    
    # Date de départ : aujourd'hui
    current_date = datetime.now().date()
    days_processed = 0
    day_offset = 0
    while days_processed < nb_days:
        day = current_date + timedelta(days=day_offset)
        day_offset += 1
        # Ne traiter que les jours de la semaine (lundi=0, ..., vendredi=4)
        if day.weekday() > 4:
            continue
        
        # Pour chaque période de la journée : matin et après‑midi
        # On attribue un rendez‑vous à une période en fonction de l'heure souhaitée dans date_debut
        # (Si l'heure souhaitée est < 12h, on l'affecte au matin, sinon à l'après‑midi)
        periods = [
            ("morning", MORNING_START, MORNING_END),
            ("afternoon", AFTERNOON_START, AFTERNOON_END)
        ]
        
        # Pour chaque période, filtrer les rendez‑vous qui concernent ce jour et cette période
        for period_name, p_start, p_end in periods:
            eligible_rdvs = []
            for rdv in appointments_mod:
                try:
                    rdv_dt = datetime.strptime(rdv["date_debut"], "%Y-%m-%dT%H:%M:%SZ")
                except Exception as e:
                    continue
                if rdv_dt.date() != day:
                    continue
                # Déterminer la période souhaitée selon l'heure de rdv_dt
                if period_name == "morning" and rdv_dt.hour < 12:
                    eligible_rdvs.append(rdv)
                elif period_name == "afternoon" and rdv_dt.hour >= 14:
                    eligible_rdvs.append(rdv)
                # Pour les rendez‑vous dont l'heure souhaitée est dans la zone de transition (entre 12h et 14h),
                # on les affecte par défaut au matin.
                elif period_name == "morning" and 12 <= rdv_dt.hour < 14:
                    eligible_rdvs.append(rdv)
            
            if not eligible_rdvs:
                continue
            
            # Optimiser cette période
            result = optimize_period_routing(eligible_rdvs, day, p_start, p_end, vehicles)
            # Mettre à jour les rendez‑vous modifiables (seuls ceux qui sont planifiés)
            for rdv in eligible_rdvs:
                rid = rdv["id_rdv"]
                if rid in result:
                    scheduled_start = result[rid]["scheduled_start"]  # minutes depuis minuit
                    # La date_debut optimisée devient la date du jour + scheduled_start
                    new_date_debut = minutes_to_time_str(day, scheduled_start)
                    new_date_fin = minutes_to_time_str(day, scheduled_start + rdv["duree"])
                    new_affectation = result[rid]["assigned_resources"]
                    # Comparer avec les valeurs actuelles et mettre à jour si différent
                    if (rdv["date_debut"] != new_date_debut or
                        rdv["date_fin"] != new_date_fin or
                        set(rdv["affectation_ressources"]) != set(new_affectation)):
                        rdv["date_debut"] = new_date_debut
                        rdv["date_fin"] = new_date_fin
                        rdv["affectation_ressources"] = new_affectation
                        updated_rdvs[rid] = rdv
        days_processed += 1
    # Retourner la liste des rendez‑vous modifiés
    return list(updated_rdvs.values())

