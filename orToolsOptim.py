from ortools.sat.python import cp_model
from datetime import datetime, timedelta

# Exemple de créneaux dynamiques
appointments = [{
    "id": "1",
    "title": "Rendez-vous Client A",
    "start": "2024-12-02T10:00:00",
    "duration": 90,
    "statut": "figé",    
    "accessibilite":"",
    "geolocalisation": (48.8566, 2.3522),
    "dateDispo": "2024-11-29"
}, {
    "id": "2",
    "title": "Appel d'équipe",
    "start": "2024-12-02T14:00:00",
    "duration": 60,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.8570, 2.3530),
    "dateDispo": "2024-11-30"
}, {
    "id": "3",
    "title": "Réunion interne",
    "start": "2024-12-03T09:00:00",
    "duration": 60,
    "statut": "modifiable",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "4",
    "title": "Nouvelle inter",
    "start": None,
    "end": None,
    "duration": 90,
    "statut": "modifiable",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "5",
    "title": "Itursarry",
    "start": "2024-12-03T10:00:00",
    "duration": 120,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.4322),
    "dateDispo": "2024-12-01"
}, {
    "id": "6",
    "title": "Teileria",
    "start": "2024-12-03T13:00:00",
    "duration": 210,
    "statut": "modifiable",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "7",
    "title": "Wagner",
    "start": "2024-12-04T08:00:00",
    "duration": 120,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 4.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "8",
    "title": "Minjou",
    "start": "2024-12-04T10:00:00",
    "duration": 120,
    "statut": "modifiable",     
    "accessibilite":"",
    "geolocalisation": (45.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "9",
    "title": "Fontan",
    "start": "2024-12-04T13:00:00",
    "duration": 90,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (46.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "10",
    "title": "Bidart",
    "start": "2024-12-04T14:30:00",
    "duration": 120,
    "statut": "modifiable",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "11",
    "title": "Emile",
    "start": "2024-12-05T08:00:00",
    "duration": 90,
    "statut": "modifiable",     
    "accessibilite":"",
    "geolocalisation": (48.5666, 5.4522),
    "dateDispo": "2024-12-01"
}, {
    "id": "12",
    "title": "Fisset",
    "start": "2024-12-05T09:30:00",
    "duration": 150,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.3422),
    "dateDispo": "2024-12-01"
}, {
    "id": "13",
    "title": "Sorin",
    "start": "2024-12-05T13:00:00",
    "duration": 60,
    "statut": "modifiable",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "14",
    "title": "Biscay",
    "start": "2024-12-05T14:00:00",
    "duration": 150,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.8566, 5.3552),
    "dateDispo": "2024-12-01"
}, {
    "id": "15",
    "title": "Anton",
    "start": "2024-12-06T08:00:00",
    "duration": 120,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.9522),
    "dateDispo": "2024-12-01"
}, {
    "id": "16",
    "title": "Lefevert",
    "start": "2024-12-06T10:00:00",
    "duration": 120,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 4.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "17",
    "title": "Boyer",
    "start": "2024-12-06T13:00:00",
    "duration": 90,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.7666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "18",
    "title": "Laborde",
    "start": "2024-12-06T14:30:00",
    "duration": 120,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (44.8666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "19",
    "title": "Anton",
    "start": "2024-12-07T08:00:00",
    "duration": 90,
    "statut": "modifiable",     
    "accessibilite":"libre",
    "geolocalisation": (48.8666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "20",
    "title": "Lefevert",
    "start": "2024-12-07T09:30:00",
    "duration": 150,
    "statut": "modifiable",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "21",
    "title": "Boyer",
    "start": "2024-12-07T13:00:00",
    "duration": 120,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.5666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "22",
    "title": "Laborde",
    "start": "2024-12-07T15:00:00",
    "duration": 90,
    "statut": "figé",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 8.3522),
    "dateDispo": "2024-12-01"
}, {
   "id": "23",
   "title": "Appel d'équipe",
   "start": "2024-12-02T08:00:00",
   "duration": 120,
   "statut": "modifiable",     
   "accessibilite":"",
   "geolocalisation": (48.8470, 2.3530),
   "dateDispo": "2024-11-30"
}, {
   "id": "24",
   "title": "Appel d'équipe",
   "start": "2024-12-02T12:30:00",
   "duration": 90,
   "statut": "figé",     
   "accessibilite":"",
   "geolocalisation": (48.8590, 2.3530),
   "dateDispo": "2024-11-30"
}]

# Ajouter le champ `end` en fonction de `start` et `duration`
for appointment in appointments:
    if appointment["start"]:
        start_time = datetime.fromisoformat(
            appointment["start"])  # Convertir `start` en datetime
        end_time = start_time + timedelta(minutes=appointment["duration"])
        appointment["end"] = end_time.isoformat()
    else:
        start_time = None
        end_time = None


#fonction principale
def optimize_schedule(appointments):
    print("Started")
    # Modèle pour l'optimisation
    model = cp_model.CpModel()
    
    # Constantes
    WORK_START = 8 * 60  # Début de la journée en minutes (8h00)
    WORK_END = 18 * 60   # Fin de la journée en minutes (18h00)
    LUNCH_START = 12 * 60  # Début de la pause déjeuner (12h00)
    LUNCH_END = 14 * 60    # Fin de la pause déjeuner (14h00)
    MINUTES_PER_DAY = WORK_END - WORK_START

    # Variables
    tasks = []
    task_starts = {}
    task_ends = {}
    task_days = {}
    max_day = 0
    
    for appointment in appointments:
        task_id = appointment["id"]
        duration = appointment["duration"]  # en minutes
        statut = appointment["statut"]
        date_dispo = datetime.strptime(appointment["dateDispo"], "%Y-%m-%d")
        day_offset = (date_dispo - datetime(2024, 1, 1)).days
        
        if statut == "figé":
            # Si l'appointement est figé, on utilise les horaires donnés
            start = datetime.strptime(appointment["start"], "%Y-%m-%dT%H:%M:%S")
            end = datetime.strptime(appointment["end"], "%Y-%m-%dT%H:%M:%S")
            day = (start - datetime(2024, 1, 1)).days
            
            # Fixer la tâche dans le modèle
            task_starts[task_id] = model.NewConstant(day * MINUTES_PER_DAY + (start.hour * 60 + start.minute))
            task_ends[task_id] = model.NewConstant(day * MINUTES_PER_DAY + (end.hour * 60 + end.minute))
            task_days[task_id] = model.NewConstant(day)
        else:
            # Variables pour un appointement modifiable
            start_var = model.NewIntVar(0, 365 * MINUTES_PER_DAY, f"start_{task_id}")
            end_var = model.NewIntVar(0, 365 * MINUTES_PER_DAY, f"end_{task_id}")
            day_var = model.NewIntVar(0, 365, f"day_{task_id}")
            

            # Contraintes pour les heures de travail (hors pause)
            start_offset = day_var * MINUTES_PER_DAY + start_var
            model.Add(start_var >= WORK_START)
            model.Add(start_var < WORK_END - duration + 60)


            # Contraintes sur les dates disponibles
            model.Add(day_var >= day_offset)
            model.Add(day_var <= day_offset + 30)

            # Contraintes sur la durée de l'appointement
            model.Add(end_var == start_var + duration)

            # Sauvegarder les variables
            task_starts[task_id] = start_var
            task_ends[task_id] = end_var
            task_days[task_id] = day_var
        
        tasks.append(task_id)
    
            # Contraintes pour éviter les chevauchements
        for i, task1 in enumerate(tasks):
            for j, task2 in enumerate(tasks):
                if i < j:
                    # Une tâche ne peut pas commencer avant la fin d'une autre
                    model.Add(task_starts[task1] >= task_ends[task2])
                    model.Add(task_starts[task2] >= task_ends[task1])
    

    # Minimiser le délai des rendez-vous déplacés
    total_delay = model.NewIntVar(0, 10000, "total_delay")
    delays = []
    for task_id in task_days:
        delay = model.NewIntVar(0, 100, f"delay_{task_id}")
        model.Add(delay >= task_days[task_id] - day_offset)
        delays.append(delay)
    model.Add(total_delay == sum(delays))
    model.Minimize(total_delay)

    # Fonction objectif : Minimiser les temps morts entre les appointements
    total_idle_time = model.NewIntVar(0, 100000, "total_idle_time")
    idle_times = []
    for i in range(len(tasks) - 1):
        idle_time = model.NewIntVar(0, 100000, f"idle_time_{i}")
        model.Add(idle_time == task_starts[tasks[i + 1]] - task_ends[tasks[i]])
        idle_times.append(idle_time)
    model.Add(total_idle_time == sum(idle_times))
    model.Minimize(total_idle_time+total_delay)

    
    # Résolution
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
     # Affichage des changements
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        optimized_appointments = []
        changes = []
        for appointment in appointments:
            task_id = appointment["id"]
            original_start = appointment["start"]
            original_end = appointment["end"]

            if task_id in task_starts:
                # Convertir les résultats optimisés
                start_time = solver.Value(task_starts[task_id])
                end_time = solver.Value(task_ends[task_id])
                day = solver.Value(task_days[task_id])
                
                # Reconvertir en datetime
                day_date = datetime(2024, 1, 1) + timedelta(days=day)
                start_datetime = day_date + timedelta(minutes=start_time)
                end_datetime = day_date + timedelta(minutes=end_time)
                
                # Sauvegarder les résultats
                optimized_appointments.append({
                    "id": task_id,
                    "start": start_datetime.isoformat(),
                    "end": end_datetime.isoformat()
                })
                
                # Vérifier les changements
                if appointment["statut"] != "figé":
                    if original_start != start_datetime.isoformat() or original_end != end_datetime.isoformat():
                        changes.append({
                            "id": task_id,
                            "original_start": original_start,
                            "original_end": original_end,
                            "new_start": start_datetime.isoformat(),
                            "new_end": end_datetime.isoformat(),
                        })
        
        # Afficher les changements
        print("\n=== Changements dans le planning ===")
        if changes:
            for change in changes:
                print(
                    f"Appointement ID: {change['id']}\n"
                    f" - Original: {change['original_start']} -> {change['original_end']}\n"
                    f" - Nouveau: {change['new_start']} -> {change['new_end']}\n"
                )
        else:
            print("Aucun changement appliqué (les appointements étaient déjà optimisés).")
        
        return optimized_appointments
    else:
        print("Aucune solution faisable trouvée.")
        return []

optimize_schedule(appointments)

print("Le script a terminé son exécution.")