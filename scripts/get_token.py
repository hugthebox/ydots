from google_auth_oauthlib.flow import InstalledAppFlow
import json, glob

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

secret_file = glob.glob("client_secret_*.json")[0]
flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
creds = flow.run_local_server(port=0)

with open("token.json", "w") as f:
    json.dump({
        "refresh_token": creds.refresh_token,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
    }, f, indent=2)

print("OK — token.json saved")
