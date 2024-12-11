from flask import Flask, jsonify, request, render_template
from datetime import datetime, timedelta
import propositionsDates
import recalculDate

app = Flask(__name__)

# Exemple de créneaux dynamiques
appointments = [{
    "id": "1",
    "title": "Rendez-vous Client A",
    "start": "2024-12-02T10:00:00",
    "duration": 90,
    "statut": "",    
    "accessibilite":"",
    "geolocalisation": (48.8566, 2.3522),
    "dateDispo": "2024-11-29"
}, {
    "id": "2",
    "title": "Appel d'équipe",
    "start": "2024-12-02T14:00:00",
    "duration": 60,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8570, 2.3530),
    "dateDispo": "2024-11-30"
}, {
    "id": "3",
    "title": "Réunion interne",
    "start": "2024-12-03T09:00:00",
    "duration": 60,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "4",
    "title": "Nouvelle inter",
    "start": None,
    "end": None,
    "duration": 90,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "5",
    "title": "Itursarry",
    "start": "2024-12-03T10:00:00",
    "duration": 120,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.4322),
    "dateDispo": "2024-12-01"
}, {
    "id": "6",
    "title": "Teileria",
    "start": "2024-12-03T13:00:00",
    "duration": 210,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "7",
    "title": "Wagner",
    "start": "2024-12-04T08:00:00",
    "duration": 120,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 4.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "8",
    "title": "Minjou",
    "start": "2024-12-04T10:00:00",
    "duration": 120,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (45.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "9",
    "title": "Fontan",
    "start": "2024-12-04T13:00:00",
    "duration": 90,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (46.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "10",
    "title": "Bidart",
    "start": "2024-12-04T14:30:00",
    "duration": 120,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "11",
    "title": "Emile",
    "start": "2024-12-05T08:00:00",
    "duration": 90,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.5666, 5.4522),
    "dateDispo": "2024-12-01"
}, {
    "id": "12",
    "title": "Fisset",
    "start": "2024-12-05T09:30:00",
    "duration": 150,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.3422),
    "dateDispo": "2024-12-01"
}, {
    "id": "13",
    "title": "Sorin",
    "start": "2024-12-05T13:00:00",
    "duration": 60,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 2.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "14",
    "title": "Biscay",
    "start": "2024-12-05T14:00:00",
    "duration": 150,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8566, 5.3552),
    "dateDispo": "2024-12-01"
}, {
    "id": "15",
    "title": "Anton",
    "start": "2024-12-06T08:00:00",
    "duration": 120,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.9522),
    "dateDispo": "2024-12-01"
}, {
    "id": "16",
    "title": "Lefevert",
    "start": "2024-12-06T10:00:00",
    "duration": 120,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 4.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "17",
    "title": "Boyer",
    "start": "2024-12-06T13:00:00",
    "duration": 90,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.7666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "18",
    "title": "Laborde",
    "start": "2024-12-06T14:30:00",
    "duration": 120,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (44.8666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "19",
    "title": "Anton",
    "start": "2024-12-07T08:00:00",
    "duration": 90,
    "statut": "",     
    "accessibilite":"libre",
    "geolocalisation": (48.8666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "20",
    "title": "Lefevert",
    "start": "2024-12-07T09:30:00",
    "duration": 150,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "21",
    "title": "Boyer",
    "start": "2024-12-07T13:00:00",
    "duration": 120,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.5666, 5.3522),
    "dateDispo": "2024-12-01"
}, {
    "id": "22",
    "title": "Laborde",
    "start": "2024-12-07T15:00:00",
    "duration": 90,
    "statut": "",     
    "accessibilite":"",
    "geolocalisation": (48.8666, 8.3522),
    "dateDispo": "2024-12-01"
}, {
   "id": "23",
   "title": "Appel d'équipe",
   "start": "2024-12-02T08:00:00",
   "duration": 120,
   "statut": "",     
   "accessibilite":"",
   "geolocalisation": (48.8470, 2.3530),
   "dateDispo": "2024-11-30"
}, {
   "id": "24",
   "title": "Appel d'équipe",
   "start": "2024-12-02T12:30:00",
   "duration": 90,
   "statut": "",     
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

print(appointments)

@app.route("/run_attribution", methods=["POST"])
def run_attribution():
    """
    Parcourt les appointments et attribue des dates optimales pour ceux qui ont `start` vide.
    """
    for appointment in appointments:
        if appointment["start"] is None:
            appointment_updated = propositionsDates.ajouter_dates(appointment, appointments)
            if appointment_updated and "start" in appointment_updated:
                appointment["start"] = appointment_updated["start"]
                appointment["end"] = appointment_updated["end"]
            else:
                print(f"Failed to update appointment {appointment['id']}")
            print(f"Appointment {appointment['id']} updated: {appointment_updated}")
            # Appelle la fonction d'attribution
        print(f"New appointment list is : {appointments}")

    return jsonify({
        "success": True,
        "appointments": appointments
    })  # Retourne l'état actuel


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/events")
def events():
    return jsonify(appointments)


@app.route("/update_event", methods=["POST"])
def update_event():
    data = request.json
    event_id = data.get("id")
    new_start = data.get("start")
    new_end = data.get("end")

    # Rechercher l'événement et mettre à jour ses données
    for appointment in appointments:
        if appointment["id"] == event_id:
            appointment["start"] = new_start
            appointment["end"] = new_end
            print(f"Créneau mis à jour : {appointments}")
            break

    return jsonify({"success": True})

@app.route("/delete_event", methods=["POST"])
def delete_event():
    data = request.json
    event_id = data.get("id")
    event_start = data.get("start")
    event_end = data.get("end")

    # Supprimer l'événement de la liste des rendez-vous
    global appointments
    appointments = [appt for appt in appointments if str(appt["id"]) != str(event_id)]
    meilleurRdv = recalculDate.caler_meilleur_appointment(event_start, event_end, appointments)
    if meilleurRdv :
        title = meilleurRdv["title"]
        for appointment in appointments:
            if appointment["id"]==meilleurRdv["id"]:
                appointment["start"] = meilleurRdv["start"]
                appointment["end"] = meilleurRdv["end"]
                print(f"Créneau mis à jour : {appointments}")
                break
        print(f"Événement avec ID={event_id} supprimé et remplacé avec RDV={title}.")
        return jsonify({"success": True})
    else : 
        print(f"Événement avec ID={event_id} supprimé.")
        return jsonify({"success": True})

    


@app.route("/update_duration", methods=["POST"])
def update_duration():
    data = request.json
    event_id = data.get("id")
    new_duration = data.get("duration")

    # Mettre à jour la durée dans appointments
    for appointment in appointments:
        if appointment["id"] == event_id:
            appointment["duration"] = new_duration
            # Recalculer la fin en fonction de la nouvelle durée
            if appointment["start"]:
                start_time = datetime.fromisoformat(
                    appointment["start"])  # Convertir `start` en datetime
                end_time = start_time + timedelta(minutes=new_duration)
                appointment["end"] = end_time.isoformat()
            else:
                start_time = None
                end_time = None
        print(f"Mise à jour de la durée : {appointment}")
        break

    return jsonify({"success": True})
print(appointments)

if __name__ == "__main__":
    app.run(debug=True)
