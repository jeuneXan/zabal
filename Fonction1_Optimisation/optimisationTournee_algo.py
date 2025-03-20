#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script complet d’optimisation de planning avec OR‑Tools

Ce script prend en entrée une liste de rendez‑vous (au format JSON ou dictionnaires)
et un nombre de jours sur lesquels optimiser le planning.
Les rendez‑vous sont optimisés par jour et par période (matin : 8h-12h, après‑midi : 14h-17h),
en respectant les fenêtres temporelles (la plage client) et la contrainte de ressources.
Les rendez‑vous modifiables verront leur créneau (date_debut_rdv, date_fin_rdv) et leur affectation
(modification du champ affectation_ressources) mis à jour.
Seuls les rendez‑vous modifiés sont renvoyés en sortie.
"""

import math
import json
from datetime import datetime, date, timedelta
from collections import defaultdict
from copy import deepcopy
from dateutil.parser import parse
from utils import haversine_distance, to_datetime

# Import OR‑Tools
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

# Capacité journalière en minutes de travail (uniquement les plages actives)
DAILY_WORK_CAPACITY = (MORNING_END - MORNING_START) + (AFTERNOON_END - AFTERNOON_START)  # 240 + 180 = 420 minutes

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
    
    La fenêtre de temps de chaque rendez‑vous est calculée en intersectant la plage d'optimisation
    avec la fenêtre souhaitée par le client (date_debut_client, date_fin_client).
    Si l'une des dates client est nulle, on utilise par défaut la borne de la période.
    """
    period_duration = period_end - period_start
    nodes = []
    node_metadata = {}  # mapping: global_node_index -> (appointment_id, copy_index)
    
    # Dépôt en position 0
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
    multi_resource_groups = defaultdict(list)
    
    for rdv in appointments:
        # Récupérer les dates client en gérant le cas null
        client_start_str = rdv.get("date_debut_client")
        client_end_str = rdv.get("date_fin_client")
        client_start_dt = to_datetime(client_start_str) if client_start_str else None
        client_end_dt = to_datetime(client_end_str) if client_end_str else None
        # Si la date de fin client est définie, on soustrait 1 minute pour la fenêtre
        if client_end_dt:
            client_end_dt = client_end_dt - timedelta(minutes=1)
        
        # Vérifier que le jour courant est dans la fenêtre client si les deux dates sont définies
        if client_start_dt and client_end_dt:
            if not (client_start_dt.date() <= day_date <= client_end_dt.date()):
                continue

        # Détermination de la borne inférieure
        if client_start_dt and client_start_dt.date() == day_date:
            desired_lower = time_to_minutes(client_start_dt)
        else:
            desired_lower = period_start  # pas de contrainte basse

        # Détermination de la borne supérieure
        if client_end_dt and client_end_dt.date() == day_date:
            desired_upper = time_to_minutes(client_end_dt)
        else:
            desired_upper = period_end  # pas de contrainte haute

        # Intersection avec la période d'optimisation
        lower_bound = max(desired_lower, period_start)
        upper_bound = min(desired_upper, period_end)
        if lower_bound > upper_bound:
            continue

        # Pour un rendez‑vous non modifiable, fixer une fenêtre très étroite
        if rdv["modifiable"] == 0:
            tw_lower = lower_bound - period_start
            tw_upper = tw_lower + 1  # fenêtre d'une minute
        else:
            tw_lower = lower_bound - period_start
            tw_upper = upper_bound - period_start

        service_time = int(rdv["duree"])
        
        # Traitement des coordonnées
        try:
            coord = parse_gps(rdv["coordonnees_gps"])
        except Exception as e:
            print(f"Erreur lors du parsing des coordonnées pour rdv id {rdv['id_rdv']}: {e}")
            continue
        
        # Déterminer les véhicules autorisés
        if rdv["modifiable"] == 0:
            allowed = [rdv["affectation_ressources"][0]]
        else:
            allowed = rdv["affectation_ressources"]
        allowed_vehicle_indices = [i for i, emp in enumerate(vehicles) if emp in allowed]
        if not allowed_vehicle_indices:
            continue
        
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
            if nb_copies > 1:
                multi_resource_groups[rdv["id_rdv"]].append(node_index)
    
    if len(nodes) <= 1:
        return {}
    
    # Construction de la matrice de temps entre tous les nœuds
    num_nodes = len(nodes)
    time_matrix = [[0] * num_nodes for _ in range(num_nodes)]
    for i in range(num_nodes):
        for j in range(num_nodes):
            coord_i = nodes[i]["coord"] if not nodes[i].get("is_depot", False) else DEPOT_COORDINATES
            coord_j = nodes[j]["coord"] if not nodes[j].get("is_depot", False) else DEPOT_COORDINATES
            time_matrix[i][j] = travel_time(coord_i, coord_j)
    
    data = {
        'time_matrix': time_matrix,
        'service_times': [node["service_time"] for node in nodes],
        'time_windows': [node["time_window"] for node in nodes],
        'allowed_vehicles': [node["allowed_vehicles"] for node in nodes],
        'num_vehicles': len(vehicles),
        'depot': 0
    }
    
    # Création du modèle OR‑Tools
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)
    
    def cost_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node   = manager.IndexToNode(to_index)
        service = data['service_times'][from_node] if from_node != data['depot'] else 0
        return data['time_matrix'][from_node][to_node] + service
    cost_callback_index = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(cost_callback_index)
    
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        service = data['service_times'][from_node] if from_node != data['depot'] else 0
        return service
    time_callback_index = routing.RegisterTransitCallback(time_callback)
    
    routing.AddDimension(
        time_callback_index,
        30,  # slack
        period_duration,  # capacité maximale
        False,  # cumul ne commence pas à 0 automatiquement
        "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    
    # Appliquer les fenêtres de temps pour chaque nœud
    for node_index in range(len(data['time_windows'])):
        index = manager.NodeToIndex(node_index)
        window = data['time_windows'][node_index]
        time_dimension.CumulVar(index).SetRange(window[0], window[1])
    
    # Restreindre les véhicules autorisés pour chaque rendez‑vous
    for node_index in range(1, len(nodes)):
        index = manager.NodeToIndex(node_index)
        allowed = data['allowed_vehicles'][node_index]
        routing.SetAllowedVehiclesForIndex(allowed, index)
    
    # Contrainte de synchronisation pour rendez‑vous multi‑ressources
    for rdv_id, node_indices in multi_resource_groups.items():
        if len(node_indices) < 2:
            continue
        for i in range(len(node_indices) - 1):
            idx1 = manager.NodeToIndex(node_indices[i])
            idx2 = manager.NodeToIndex(node_indices[i+1])
            routing.solver().Add(time_dimension.CumulVar(idx1) == time_dimension.CumulVar(idx2))
    
    # Disjonctions pour favoriser la visite des rendez‑vous
    for node_index in range(1, len(nodes)):
        routing.AddDisjunction([manager.NodeToIndex(node_index)], SKIP_PENALTY)
    
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.FromSeconds(TIME_LIMIT)
    
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        print(f"Aucune solution trouvée pour la période {period_start}-{period_end} le {day_date}")
        return {}
    
    result = defaultdict(lambda: {"scheduled_start": None, "assigned_resources": set()})
    visited_nodes = set()
    for veh in range(data['num_vehicles']):
        index = routing.Start(veh)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != data['depot']:
                visited_nodes.add(node)
                t_var = time_dimension.CumulVar(index)
                scheduled_relative = solution.Value(t_var)
                scheduled_absolute = period_start + scheduled_relative  # minutes depuis minuit
                rdv_id, copy_index = node_metadata[node]
                result[rdv_id]["assigned_resources"].add(vehicles[veh])
                result[rdv_id]["scheduled_start"] = scheduled_absolute
            index = solution.Value(routing.NextVar(index))
    
    for rdv_id in result:
        result[rdv_id]["assigned_resources"] = list(result[rdv_id]["assigned_resources"])
    
    # Limiter le nombre de ressources assignées au nombre requis
    for rdv in appointments:
        rid = rdv["id_rdv"]
        if rid in result:
            required = int(rdv.get("nombre_ressources", 1))
            if len(result[rid]["assigned_resources"]) > required:
                result[rid]["assigned_resources"] = result[rid]["assigned_resources"][:required]
    
    # Pour les rendez‑vous multi‑ressources, supprimer ceux dont toutes les copies n'ont pas été visitées
    for rdv_id, node_indices in multi_resource_groups.items():
        all_visited = all(n in visited_nodes for n in node_indices)
        if not all_visited and rdv_id in result:
            del result[rdv_id]
    
    return result

# --------------------------
# OPTIMISATION SUR L'HORIZON (PLUSIEURS JOURS)
# --------------------------
def optimize_schedule(appointments, nb_days):
    """
    Optimise le planning sur nb_days jours (du jour courant jusqu'à aujourd'hui + nb_days),
    en considérant uniquement les jours travaillés (lundi à vendredi).

    appointments : liste de dictionnaires correspondant aux rendez‑vous.
    Retourne une liste (de dictionnaires JSON) contenant uniquement les rendez‑vous modifiés,
    avec mise à jour des champs "date_debut_rdv", "date_fin_rdv" et "affectation_ressources".
    """
    # Construction de la liste globale des employés
    vehicles_set = set()
    for rdv in appointments:
        for emp in rdv["affectation_ressources"]:
            vehicles_set.add(emp)
    vehicles = sorted(list(vehicles_set))
    
    appointments_mod = deepcopy(appointments)
    updated_rdvs = {}
    
    # Pré‑traitement pour les rendez‑vous multi‑journée :
    # Si la durée dépasse la capacité journalière (420 minutes), on planifie sur plusieurs jours.
    for rdv in appointments_mod:
        duration = int(rdv["duree"])
        if duration > DAILY_WORK_CAPACITY:
            nb_required_days = math.ceil(duration / DAILY_WORK_CAPACITY)
            # Début de planification : utiliser le maximum entre aujourd'hui et date_debut_client si définie
            client_start_str = rdv.get("date_debut_client")
            if client_start_str:
                client_start_date = to_datetime(client_start_str).date()
            else:
                client_start_date = datetime.now().date()
            client_end_str = rdv.get("date_fin_client")
            if client_end_str:
                client_end_date = to_datetime(client_end_str).date()
            else:
                client_end_date = None  # pas de borne haute client
            
            current_date = max(datetime.now().date(), client_start_date)
            scheduled_dates = []
            days_planned = 0
            while days_planned < nb_required_days:
                if current_date.weekday() < 5:
                    scheduled_dates.append(current_date)
                    days_planned += 1
                current_date += timedelta(days=1)
            rdv["date_debut_rdv"] = minutes_to_time_str(scheduled_dates[0], MORNING_START)
            reste = duration - DAILY_WORK_CAPACITY * (nb_required_days - 1)
            if reste >= (AFTERNOON_END - AFTERNOON_START):
                rdv["date_fin_rdv"] = minutes_to_time_str(scheduled_dates[-1], AFTERNOON_END)
            else:
                rdv["date_fin_rdv"] = minutes_to_time_str(scheduled_dates[-1], MORNING_START + reste)
            updated_rdvs[rdv["id_rdv"]] = rdv
            rdv["skip_optim"] = True  # marquer pour ne pas réoptimiser
        else:
            rdv["skip_optim"] = False

    # Optimisation sur l'horizon
    days_processed = 0
    day_offset = 0
    current_date = datetime.now().date()
    while days_processed < nb_days:
        day = current_date + timedelta(days=day_offset)
        day_offset += 1
        if day.weekday() > 4:
            continue  # ignorer week-end
        
        periods = [
            ("morning", MORNING_START, MORNING_END),
            ("afternoon", AFTERNOON_START, AFTERNOON_END)
        ]
        for period_name, p_start, p_end in periods:
            eligible_rdvs = []
            for rdv in appointments_mod:
                if rdv.get("skip_optim", False):
                    continue
                # Vérifier la contrainte de fenêtre client si définie
                client_start_str = rdv.get("date_debut_client")
                client_end_str = rdv.get("date_fin_client")
                if client_start_str:
                    client_start_date = to_datetime(client_start_str).date()
                else:
                    client_start_date = None
                if client_end_str:
                    client_end_date = to_datetime(client_end_str).date()
                else:
                    client_end_date = None
                # Si les deux sont définies, le jour doit être compris dans la fenêtre
                if client_start_date and client_end_date:
                    if not (client_start_date <= day <= client_end_date):
                        continue

                rdv_client_dt = to_datetime(rdv["date_debut_client"]) if rdv.get("date_debut_client") else None
                # Si la date de début client est définie, déterminer la période
                if rdv_client_dt:
                    if period_name == "morning" and rdv_client_dt.hour < 12:
                        eligible_rdvs.append(rdv)
                    elif period_name == "afternoon" and rdv_client_dt.hour >= 14:
                        eligible_rdvs.append(rdv)
                    elif period_name == "morning" and 12 <= rdv_client_dt.hour < 14:
                        eligible_rdvs.append(rdv)
                else:
                    # Si non défini, on considère le rendez‑vous éligible
                    eligible_rdvs.append(rdv)
            if not eligible_rdvs:
                continue
            result = optimize_period_routing(eligible_rdvs, day, p_start, p_end, vehicles)
            for rdv in eligible_rdvs:
                rid = rdv["id_rdv"]
                if rid in result:
                    scheduled_start = result[rid]["scheduled_start"]  # minutes depuis minuit
                    new_date_debut_rdv = minutes_to_time_str(day, scheduled_start)
                    new_date_fin_rdv = minutes_to_time_str(day, scheduled_start + int(rdv["duree"]))
                    new_affectation = result[rid]["assigned_resources"]
                    if (rdv.get("date_debut_rdv") != new_date_debut_rdv or
                        rdv.get("date_fin_rdv") != new_date_fin_rdv or
                        set(rdv["affectation_ressources"]) != set(new_affectation)):
                        rdv["date_debut_rdv"] = new_date_debut_rdv
                        rdv["date_fin_rdv"] = new_date_fin_rdv
                        rdv["affectation_ressources"] = new_affectation
                        updated_rdvs[rid] = rdv
        days_processed += 1
    return list(updated_rdvs.values())

# --------------------------
# EXEMPLE D'UTILISATION
# --------------------------
'''
if __name__ == "__main__":
    # Exemple de rendez‑vous
    appointments = [
        {
            "id_rdv": 11673,
            "modifiable": 1,
            "duree": "16",  # durée en minutes ou convertie en minutes
            "nombre_ressources": 1,
            "coordonnees_gps": "43.481930, -1.518339",
            # Les anciens champs remplacés par les 4 nouveaux :
            "date_debut_rdv": None,
            "date_fin_rdv": None,
            "date_debut_client": "2025-02-18T08:00:00",
            "date_fin_client": "2025-02-19T17:00:00"
        },
        # ... d'autres rendez‑vous
    ]
    
    nb_days = 3
    modified_appointments = optimize_schedule(appointments, nb_days)
    print("Rendez‑vous modifiés :")
    print(json.dumps(modified_appointments, indent=4))
'''
