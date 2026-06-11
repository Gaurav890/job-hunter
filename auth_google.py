"""
Run this ONCE locally to generate your Google OAuth2 refresh token.

    python auth_google.py

A browser window will open — sign in with your Gmail and approve access.
It will print 3 values to paste into your .env and Railway env vars.
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret_403573419172-ulp6podshmkg6a5tdd1nchs54vb4f7i4.apps.googleusercontent.com.json",
    SCOPES,
)
creds = flow.run_local_server(port=0)

print("\n" + "="*55)
print("Add these to your .env AND Railway environment variables:")
print("="*55)
print(f"GOOGLE_CLIENT_ID={creds.client_id}")
print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
print("="*55)
