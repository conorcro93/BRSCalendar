import os
import sys
from configparser import ConfigParser
import json
from GoogleCalendarAPI import GoogleCalendarAPI
from BRSAPI import BRSAPI

SCOPES = ['https://www.googleapis.com/auth/calendar']  # If modifying these scopes, delete the file token.pickle.
CONFIGURATION_FILE = 'configuration.ini'
GOOGLE_CREDENTIALS_FILE = 'google_credentials.json'
BRS_CREDENTIALS_FILE = 'brs_credentials.json'

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    config = ConfigParser()
    config.read(CONFIGURATION_FILE)
    DRIVER = config.get('driver', 'driver')
    DRIVER_BROWSER = config.get(DRIVER, 'browser')
    DRIVER_PATH = config.get(DRIVER, 'path')
    calendar_name = config.get('calendar', 'name')
    event_name = config.get('calendar', 'event_name')
    event_location = config.get('calendar', 'location')

    with open(BRS_CREDENTIALS_FILE, 'r') as f:
        brs_credentials = json.load(f)
        brs_username = brs_credentials['username']
        brs_password = brs_credentials['password']

    google_calendar = GoogleCalendarAPI(GOOGLE_CREDENTIALS_FILE, SCOPES)
    calendar = google_calendar.get_calendar(calendar_name)
    if calendar:
        calendar_id = calendar['id']
        google_calendar.set_calendar(calendar_id)
    #else:
    # log error and exit program
    events = google_calendar.list_events()

    brs = BRSAPI(
        browser=DRIVER_BROWSER,
        driver=resource_path(DRIVER_PATH)
    )
    brs.login(
        username=brs_username,
        password=brs_password
    )
    booking_details = brs.get_booking_details()

    events = [event for event in events if event.get('summary', '') == event_name]

    booking_times = [(x['start_datetime'], x['end_datetime']) for x in booking_details]
    booking_descriptions = [x['description'] for x in booking_details]
    events_to_delete = []
    for event in events:
        if (event['info']['start_datetime'], event['info']['end_datetime']) not in booking_times:
            events_to_delete.append(event)
        elif event['info']['description'] not in booking_descriptions:
            events_to_delete.append(event)
    for event in events_to_delete:
        google_calendar.delete_event(event_id=event['id'])
        events.remove(event)

    event_times = [(event['info']['start_datetime'], event['info']['end_datetime']) for event in events]
    bookings_to_add = []
    for booking in booking_details:
        if (booking['start_datetime'], booking['end_datetime']) not in event_times:
            google_calendar.create_event(
                start_datetime=booking['start_datetime'],
                end_datetime=booking['end_datetime'],
                summary=event_name,
                description=booking['description'],
                location=event_location,
                notifications=[{'method': 'popup', 'minutes': 1440}]
            )

    brs.quit()
