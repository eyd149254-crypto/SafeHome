import os
import json
import asyncio
import time

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import firebase_admin
from firebase_admin import credentials, messaging

# =========================================================
# FASTAPI INIT
# =========================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# FIREBASE INIT
# =========================================================
if not firebase_admin._apps:
    cred_dict = {
        "type": "service_account",
        "project_id": "safehome-22c06",
        "private_key_id": "ed2bf0c060ff8eb43c3a592d0efd425fa0a5c87d",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDMPlqbDx3/jYn0\n+DOmcWrjxT3kq1RPMXx51V55qIGZy1gghoT5SmP4p/mjV159OnlZqdQEWx/saNoP\neIrDdTM0ms7SRBLPpev+KTDDDVhq+mUtaLnGj5RRSVN24gTZo3tmlLQrBlhwYeIJ\nR3Dy9Gab55jhy/ttLaz3rSk1fbHiPPbet9/pdEVgHzek9g4QjV03ucGRfDetMaTr\ncnDSRgHMdHDCAIzIuaxpo3T/s9Gvz+oGC71ZvIn5P4+yxXFm2ZHMSbHqqoBDzx5e\nxihzhyRGL+QxBFEW4sxjpzmL2Y9FjWbLAnveAOaILIuS6WWFq7wNTg1F5x2IJceE\nfHbIPbmvAgMBAAECggEAATUQe3zvxtjE1dN5GHa3f0+BxjUzf6geD6IUaWI94lHJ\nqp//KDlpg1AKbeM+tiDmaYJvwjqcVMCwzUljEQom7EdKpjvdxws4pYDK8GJxiExZ\n1N2a/4Rqh77rfeGvI4tPrSVGbyPIoQunhORpRVdEKY+lu926ayD2C4CGssb37dKw\nuR7eIplj6rEypZ1grq47IrpjsKSDNiG0z0KSiGW9EY0DAIoioIz4DAFAV9QU6MR8\n+wk7Ki45yJnTeOeaJJDdBBA3TZHt/YiwFnpUogMYXL294M9zD5rjQQheTQmnaiJK\nwCzRd+kgmmgPbibHveqnDThOuZdy7TtoxQAi4g2j4QKBgQDxpIjcA0liWNBfDjm+\nKrEWFFLoq50U1zxzpvVkBXA67lOp6FM7gk+WOOQEYvajFM+UPN0cYZtRh8p0LhKn\nGPblzUl45HV8JUDAvHknVJbYmEpj5S5zlZY2p3lQmYXJho3T3xhfubL9D+bY8Bsy\ndQJ49vcZhJBAwjaDrmVNhVI8oQKBgQDYYPdMpkUgSOlw2fpFXAYIKm8gBtDzfaTU\nZ+JnnIZjloVyFSvnayyQiRpCHhePL930XsILtzhWL2liZ9RZ7L0Y3Kr0CPQkFXGT\nYexgPPdRQfcCAXVlH60o7vuTgQYegvI2ksQzYHNQPnOM1BUEFtNIYoCMN7vr2k8C\n81bvbFqETwKBgQCiLYyRJT+OWw9WjMSiZiK+L9vJPszJXP+8mzSc8a12T9gk88FQ\n8k+aAgq/CvB/WYtL8WFxF+1XVezB9t4b+fxTFWmXUrWrIZGJCbXCeNpY+jULQJjh\niGbtvY8FUlRhggYUSeog7RA9GfwUY2nNfoyvRQlovfjXDcHqtRRWaAFeoQKBgQDV\nob7oJY1AV9xrODt5uWaXL1Yx96jbjmRr9fk5tPeWYal1PmPvgwgn18VeHBnEnEz2\nlYveR1JO/VZ9+udUtYDpiA0dDa4F5koRanAXgHnp90fp6gi/A6xSKsmmE5A4Fa8Q\npI0j8IlJY69wDoCFXgfSgrZKOkjGju7NifV+Q6uGzwKBgQDpUZ/D+CXrS6xWvw00\nHPbudksl9b0K5WYFuKdYyl4Ldrbysx798H0f0sjnqE2bJ3J+1g/i5CrOoCLkWeIj\nA87ANzHjvAUGnUJrxX1Ye/vH3w+bbdtboy2im8ypoiCRIxysw9aPUpQ+yprqaeRr\ngFzsBZiK9xUXrCBP19RLx/Jjtw==\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk-fbsvc@safehome-22c06.iam.gserviceaccount.com",
        "client_id": "102725483848353844388",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40safehome-22c06.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

client_tokens = set()
active_connections = set()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/firebase-messaging-sw.js")
async def sw():
    return FileResponse("firebase-messaging-sw.js")

@app.post("/register_token")
async def register_token(request: Request):
    data = await request.json()
    token = data.get("token")
    if not token:
        return JSONResponse({"status": "error", "message": "token invalide"}, status_code=400)
    client_tokens.add(token)
    return {"status": "ok"}

@app.post("/alert")
async def alert(request: Request):
    data = await request.json()
    alert_type = data.get("type", "").lower()
    location = data.get("location", "Lieu inconnu") # <--- Capture location from ESP32

    print("\n==============================")
    print("📩 ALERT RECEIVED")
    print(f"Type: {alert_type} | Location: {location}")
    print("==============================\n")

    if alert_type == "gas":
        title = "🚨 Fuite de gaz détectée"
        body = "Danger de gaz détecté."
    elif alert_type == "fire":
        title = "🔥 Incendie détecté"
        body = "Fumée ou feu détecté."
    else:
        title = "⚠️ Alerte inconnue"
        body = "Événement non identifié."

    # Firebase Push (Combine body + location for the phone notification)
    results = []
    start_time = time.time()
    for token in list(client_tokens):
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=f"{body} à : {location}" # <--- Add location here
                ),
                token=token
            )
            response = messaging.send(message)
            results.append({"token": token, "status": "ok"})
        except Exception as e:
            results.append({"token": token, "status": "error", "error": str(e)})

    # WebSocket Push (Send as separate field for professional UI display)
    dead = []
    for ws in active_connections:
        try:
            await ws.send_json({"title": title, "body": body, "location": location})
        except Exception as e:
            dead.append(ws)
    for ws in dead:
        active_connections.discard(ws)

    return {"status": "ok", "title": title, "body": body, "location": location}

@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except Exception:
        pass
    finally:
        active_connections.discard(websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
