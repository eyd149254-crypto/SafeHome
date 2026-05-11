import requests
import time
import urllib3

# Désactive l'avertissement SSL pour certificat auto-signé
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL de ton serveur FastAPI en local
SERVER_URL = "https://127.0.0.1:8000/alert"

# Types d'alertes à tester
alert_types = ["gas", "fire"]

def send_alert(alert_type):
    payload = {"type": alert_type}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(SERVER_URL, json=payload, headers=headers, verify=False)  # ← verify=False
        print(f"Envoyé: {alert_type} | Réponse: {response.status_code} {response.json()}")
    except Exception as e:
        print("Erreur:", e)

if __name__ == "__main__":
    i = 0
    while True:
        alert = alert_types[i % len(alert_types)]
        send_alert(alert)
        i += 1
        time.sleep(10)  # toutes les 10 secondes