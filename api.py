from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, conint, constr, root_validator
from datetime import datetime

# Importer la fonction de traitement d'optimisation
from Fonction1_Optimisation.optimisation_handler import run_optimisation

app = FastAPI()

# Gestion personnalisée des erreurs de validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"fonctionLancee": 0, "message": exc.errors()}
    )

# =====================
# Définition des modèles
# =====================

# Pour /optimisation
class OptimizationRequest(BaseModel):
    nbJours: conint(gt=0)

# Pour /remplacement-ressource
class ResourceReplacementRequest(BaseModel):
    employeAbsent: str
    dateDebut: datetime
    dateFin: datetime

    @root_validator(skip_on_failure=True)
    def check_dates(cls, values):
        date_debut = values.get("dateDebut")
        date_fin = values.get("dateFin")
        if date_debut and date_fin and date_debut > date_fin:
            raise ValueError("dateDebut doit être antérieure à dateFin")
        return values

# Pour /remplacement-rdv
position_regex = r'^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$'

class AppointmentReplacementRequest(BaseModel):
    employe: str
    dateDebut: datetime
    dateFin: datetime
    positionAvant: constr(pattern=position_regex)
    positionApres: constr(pattern=position_regex)

    @root_validator(skip_on_failure=True)
    def check_dates(cls, values):
        date_debut = values.get("dateDebut")
        date_fin = values.get("dateFin")
        if date_debut and date_fin and date_debut > date_fin:
            raise ValueError("dateDebut doit être antérieure à dateFin")
        return values

# =====================
# Définition des endpoints
# =====================

@app.post("/optimisation")
async def optimisation(request_data: OptimizationRequest):
    # Convertir l'objet Pydantic en dictionnaire
    input_data = request_data.dict()
    # Appeler la fonction d'optimisation (qui enchaîne tri puis algorithme)
    result = run_optimisation(input_data)
    return {"fonctionLancee": 1, "message": "Optimisation terminée", "result": result}

@app.post("/remplacement-ressource")
async def remplacement_ressource(request_data: ResourceReplacementRequest):
    print(
        f"Remplacement de la ressource pour l'employé {request_data.employeAbsent} "
        f"du {request_data.dateDebut} au {request_data.dateFin}."
    )
    return {"fonctionLancee": 1, "message": "Tout est OK"}

@app.post("/remplacement-rdv")
async def remplacement_rdv(request_data: AppointmentReplacementRequest):
    print(
        f"Remplacement du rendez-vous pour l'employé {request_data.employe} "
        f"du {request_data.dateDebut} au {request_data.dateFin}."
    )
    print(
        f"Créneau : position avant {request_data.positionAvant}, position après {request_data.positionApres}."
    )
    return {"fonctionLancee": 1, "message": "Tout est OK"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
