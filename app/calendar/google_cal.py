import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def check_availability(date: str, time: str, duration_hours: int = 1) -> bool:
    # returns True if the slot is free, False if something is already booked
    service = get_calendar_service()
    start_dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + datetime.timedelta(hours=duration_hours)

    # query calendar for any overlapping events
    result = service.events().list(
        calendarId="primary",
        timeMin=start_dt.strftime("%Y-%m-%dT%H:%M:%S-04:00"),
        timeMax=end_dt.strftime("%Y-%m-%dT%H:%M:%S-04:00"),
        singleEvents=True,
    ).execute()

    return len(result.get("items", [])) == 0


def find_next_available(date: str, time: str, duration_hours: int = 1):
    # finds the next open 1-hour slot starting from the given date/time
    # returns (date_str, time_str) or (None, None) if nothing found in 7 days
    start_dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    start_dt += datetime.timedelta(minutes=30)  # start checking from next half-hour

    for _ in range(200):  # safety limit
        # skip weekends
        if start_dt.weekday() >= 5:
            days_ahead = 7 - start_dt.weekday()
            start_dt = (start_dt + datetime.timedelta(days=days_ahead)).replace(hour=9, minute=0)
            continue

        # if before clinic hours, jump to 9am
        if start_dt.hour < 9:
            start_dt = start_dt.replace(hour=9, minute=0)

        # if at or after 5pm, jump to next weekday 9am
        if start_dt.hour >= 17:
            start_dt = (start_dt + datetime.timedelta(days=1)).replace(hour=9, minute=0)
            continue

        date_str = start_dt.strftime("%Y-%m-%d")
        time_str = start_dt.strftime("%H:%M")

        if check_availability(date_str, time_str, duration_hours):
            return date_str, time_str

        start_dt += datetime.timedelta(minutes=30)

    return None, None


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
    service = get_calendar_service()
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return True