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
# FIREBASE INIT — CREDENTIALS HARDCODÉES (DEMO)
# =========================================================

if not firebase_admin._apps:

    cred_dict = {
        "type": "service_account",
        "project_id": "safehome-22c06",
        "private_key_id": "af6ef0587fe1ec928619d80327db191657593c21",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC65G52R0tTByKV\nzz8RS1LyAFvGZPlnkx3KvjPsz1+/hqWxHxk6nB68lLKoXvs9pugWPV1+1Nyd1Yac\n1+Nm9YLF0Wd+d41TGj5LFIAOrzfcSFTc9YZcCwrRRC+u3iJ9Eka5v3OpQQfjCpq7\neFZLV8GzWBHfeOuEwkravp6ZzvDF/OVcPVXVNpMK693ULMnoPfhGpt1G735jLE5P\nydguy5z5M2ZmwJAWmFhCOnLet2pqy0fx3NGXzuogmzeVrWDASEDGxVbhU8cwlrr9\nz4bJ2uRQ1leDE1/lbRnyQxAFaDhSeoMenVHtIWHjRlyNGjaXiWewkf6yT4kpUdSV\nbPYe10JPAgMBAAECggEAITzyFlAMqeoJcRpILaO3TznYGJsprg2AjWexZWrmLPJd\n8nfE7WMJpmFNutsVlLvj59ynDaD+0YVBqRBOLaf5R4Q8A0Zw2HhA3up48eOgrCkj\nCp8R87m1BU26qz9vY84FzRArGk1qASuIJFI9Cq5DUUmW+CcRv+0sEeY338Ppl1Ra\nh0XLrHW/xysKY8rn+3vfqSHDX4nHAhdReKkdGrGJ9svZpIhhcCmEWLDeyX750q12\nUihwP4sX/2Oeaz8fXOFMlgzqm/bS+kZJp2K+N5f6WGu2IOD/eLjpaOKk+Zn3yd5N\nyMFeTpsCovgDdm3u5sQFX2ehMpcuwK6w7xCt/hvCCQKBgQDe0L3xYQdDuTh/UaCe\n/QPrlJuMN2XFaMEbGc+rYekjyM91SiHlX6jVBOImetHQEH44f3uG4tzSgw9l55Dp\nu7paCXnBa3Ej3iNrTGCU+CQbQcs78vHz14MX5Y9ej4zxe2euE8A4t1c6oe3k2Q36\neG2Qv3A84RjRuT5eHp0KTTaw6QKBgQDWug3OsAFP75pcrfxPJpOJymdgzVuFQZMV\nx5tcsmHRBrUAObt+vfFsXuPV3XYQN/F4kwM+muk0+0NzyZkbhvYWdZJ3/6IcABzt\nzqiY98i7MNg0jlDVm6Cq7zE4R76gk8CS+UoJtxWEXyATq4oA9RrCpiAKqqXV0+oA\n3SaAYx8WdwKBgHZT/MtXb/gzQSG8Q8SrMY3GWeTY9p8jxomR54tob9ulJSdwuxeI\n+axG76LnzszkNWPjr8IucH8LQv4nP/ogzBJMvfBOEsOtkLnG0fPK48Hl6vxnRL7u\nUJw8OStKqNsFYkY8DvUPyK9Gl4PVEWtW0TjxsbVjBT87VTe+oj96SfUhAoGAFC7I\nvXStquXKjIuN+6KUm476yI6E27GeMZ3hbIUXzJ3kxXCnvvH7j0QcBi4ausuHVt36\noBfPc7tqS6fXTE8TMmk6qyzL//XCwld6YWZo569foxD9aBaIs4hoB/I2aMF6iFYG\nL4OV8is+yJqHDi/7o/AZcuc3TzHr/MjMpaSrd2ECgYBV+z7N1ce1eZ0Xf+Wm1wt9\nSDztTzdYYwfCQCHd1m7nobECgO4lQYwY4a2lhCpe4PdCI/C4W/v5FxlGSktjMJR5\nIu+aMtiazniPRrWIvDCG2WYaGpIk/t+LwUm/zHOQVTmumCj+EfxxFBWW0pDMbLcM\nvGOmTyijszGU11K/iwm4rA==\n-----END PRIVATE KEY-----\n",
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
