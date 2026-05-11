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


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# FIREBASE INIT DEPUIS VARIABLE D'ENVIRONNEMENT
# =========================================================

if not firebase_admin._apps:

    # Sur Railway : FIREBASE_CREDENTIALS contient le JSON complet en string
    firebase_json = os.environ.get("FIREBASE_CREDENTIALS")

    if firebase_json:
        # Production (Railway) : on lit depuis la variable d'env
        cred_dict = json.loads(firebase_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # Local : on lit depuis le fichier JSON
        cred_path = os.path.join(
            os.path.dirname(__file__),
            "safehome-22c06-firebase-adminsdk-fbsvc-af6ef0587f.json"
        )
        cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(cred)


# =========================================================
# STORAGE
# =========================================================

client_tokens = set()
active_connections = set()


# =========================================================
# STATIC FILES
# =========================================================

app.mount("/static", StaticFiles(directory="static"), name="static")


# =========================================================
# HOME
# =========================================================

@app.get("/")
async def root():
    return FileResponse("static/index.html")


# =========================================================
# FIREBASE SW
# =========================================================

@app.get("/firebase-messaging-sw.js")
async def sw():
    return FileResponse("firebase-messaging-sw.js")


# =========================================================
# REGISTER TOKEN
# =========================================================

@app.post("/register_token")
async def register_token(request: Request):

    data = await request.json()
    token = data.get("token")

    if not token:
        return JSONResponse(
            {"status": "error", "message": "token invalide"},
            status_code=400
        )

    client_tokens.add(token)

    print("\n==============================")
    print("✅ TOKEN REGISTERED")
    print(token)
    print("==============================\n")

    return {"status": "ok"}


# =========================================================
# ALERT SYSTEM
# =========================================================

@app.post("/alert")
async def alert(request: Request):

    data = await request.json()
    alert_type = data.get("type", "").lower()

    print("\n==============================")
    print("📩 ALERT RECEIVED")
    print(data)
    print("==============================\n")


    # =====================================================
    # MESSAGE TYPE
    # =====================================================

    if alert_type == "gas":
        title = "🚨 Fuite de gaz détectée"
        body = "Danger de gaz dans la cuisine."

    elif alert_type == "fire":
        title = "🔥 Incendie détecté"
        body = "Fumée ou feu détecté dans la cuisine."

    else:
        title = "⚠️ Alerte inconnue"
        body = "Événement non identifié."


    # =====================================================
    # FIREBASE PUSH
    # =====================================================

    results = []
    start_time = time.time()

    for token in list(client_tokens):

        try:

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                token=token
            )

            response = messaging.send(message)
            duration = round((time.time() - start_time) * 1000, 2)

            print("\n==============================")
            print("🔥 FCM SENT SUCCESS")
            print(f"📨 Title: {title}")
            print(f"📱 Token: {token[:25]}...")
            print(f"🆔 Response: {response}")
            print(f"⏱️ Time: {duration} ms")
            print("==============================\n")

            results.append({
                "token": token,
                "status": "ok",
                "firebase_response": response,
                "time_ms": duration
            })

        except Exception as e:

            print("\n==============================")
            print("❌ FCM FAILED")
            print(f"📱 Token: {token[:25]}...")
            print(f"⚠️ Error: {str(e)}")
            print("==============================\n")

            results.append({
                "token": token,
                "status": "error",
                "error": str(e)
            })


    # =====================================================
    # WEBSOCKET PUSH
    # =====================================================

    dead = []

    for ws in active_connections:
        try:
            await ws.send_json({"title": title, "body": body})
        except Exception as e:
            print("❌ WS error:", e)
            dead.append(ws)

    for ws in dead:
        active_connections.discard(ws)


    # =====================================================
    # RESPONSE
    # =====================================================

    return {
        "status": "ok",
        "title": title,
        "body": body,
        "tokens": len(client_tokens),
        "clients": len(active_connections),
        "results": results
    }


# =========================================================
# WEBSOCKET
# =========================================================

@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):

    await websocket.accept()
    active_connections.add(websocket)

    print("🟢 WS CLIENT CONNECTED")

    try:
        while True:
            await asyncio.sleep(1)

    except Exception:
        pass

    finally:
        active_connections.discard(websocket)
        print("🔴 WS CLIENT DISCONNECTED")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )
