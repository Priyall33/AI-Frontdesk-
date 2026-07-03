import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# defines what we are allowed to do with the calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# paths to credentials files
CREDENTIALS_FILE = "credentials.json"   # downloaded from Google Cloud
TOKEN_FILE = "token.json"               # created automatically after first login

def get_calendar_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # if no valid token, ask the user to log in via browser
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # save token so we don't have to log in every time
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def create_event(summary: str, date: str, time: str, duration_hours: int = 1, description: str = ""):
   
    service = get_calendar_service()

    start_dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + datetime.timedelta(hours=duration_hours)

    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "America/New_York"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "America/New_York"},
    }

    created = service.events().insert(calendarId="primary", body=event).execute()
    print(f"Event created: {created.get('htmlLink')}")
    return created


def list_events(max_results: int = 10):

    service = get_calendar_service()
    now = datetime.datetime.utcnow().isoformat() + "Z"

    result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return result.get("items", [])


def cancel_event(event_id: str):
    # deletes an event by its ID
    service = get_calendar_service()
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    print(f"Event {event_id} cancelled")
    return True
