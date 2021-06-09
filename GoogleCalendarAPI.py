from datetime import datetime, timedelta
import pickle
import os.path
from dateutil import parser

import googleapiclient
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class GoogleCalendarAPI:
    calendar_id = 'primary'

    def __init__(self,
                 credentials_file,
                 scopes
                 ):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                creds.expiry = None
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, scopes)
                creds = flow.run_local_server(port=0)
                creds.expiry = None

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)

        self.calendars = self.list_calendars()

    def list_calendars(self,
                       print_results=False
                       ):
        print('Getting list of calendars') # debug statement
        calendars_result = self.service.calendarList().list().execute()

        calendars = calendars_result.get('items', [])

        if print_results:
            if not calendars:
                print('No calendars found.')
            for calendar in calendars:
                summary = calendar['summary']
                id = calendar['id']
                primary = "Primary" if calendar.get('primary') else ""
                print("%s\t%s\t%s" % (summary, id, primary))

        return calendars

    def get_calendar(self,
                     calendar_name,
                     print_results=False
                     ):
        calendar = next(filter(lambda x: x['summary'] == calendar_name, self.calendars), None)

        if print_results:
            if not calendar:
                print('No calendars found.')
            summary = calendar['summary']
            id = calendar['id']
            primary = "Primary" if calendar.get('primary') else ""
            print("%s\t%s\t%s" % (summary, id, primary))

        return calendar

    def set_calendar(self,
                     calendar_id
                     ):
        self.calendar_id = calendar_id

    def list_events(self,
                    calendar_id=None,
                    start_date_utc=datetime.utcnow(),
                    num_results=20,
                    print_results=False
                    ):
        start_date_iso = start_date_utc.isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting List of events')
        events_result = self.service.events().list(
            calendarId=calendar_id if calendar_id else self.calendar_id,
            timeMin=start_date_iso,
            maxResults=num_results,
            singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])

        if print_results:
            if not events:
                print('No upcoming events found.')
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(start, event['summary'])

        for event in events:
            event['info'] = self.extract_event_info(event)

        return events

    def create_event(self,
                     start_datetime,
                     end_datetime,
                     summary,
                     description,
                     location,
                     notifications,
                     calendar_id=None,
                     print_results=False
                     ):
        start_datetime_iso = start_datetime.isoformat()
        end_datetime_iso = end_datetime.isoformat()

        event_result = self.service.events().insert(
            calendarId=calendar_id if calendar_id else self.calendar_id,
            body={
                "summary": summary,
                "description": description,
                "location": location,
                "start": {"dateTime": start_datetime_iso, "timeZone": 'GMT+1:00'},
                "end": {"dateTime": end_datetime_iso, "timeZone": 'GMT+1:00'},
                "reminders": {"useDefault": False, "overrides": notifications},
            }
        ).execute()

        if print_results:
            print("created event")
            print("id: ", event_result['id'])
            print("summary: ", event_result['summary'])
            print("starts at: ", event_result['start']['dateTime'])
            print("ends at: ", event_result['end']['dateTime'])

        return event_result

    def update_event(self,
                     event_id,
                     start_datetime,
                     end_datetime,
                     summary,
                     description,
                     location,
                     calendar_id=None,
                     print_results=False
                     ):
        start_datetime_iso = start_datetime.isoformat()
        end_datetime_iso = end_datetime.isoformat()

        event_result = self.service.events().update(
            calendarId=calendar_id if calendar_id else self.calendar_id,
            eventId=event_id,
            body={
                "summary": summary,
                "description": description,
                "location": location,
                "start": {"dateTime": start_datetime_iso, "timeZone": 'GMT+1:00'},
                "end": {"dateTime": end_datetime_iso, "timeZone": 'GMT+1:00'},
            },
        ).execute()

        if print_results:
            print("updated event")
            print("id: ", event_result['id'])
            print("summary: ", event_result['summary'])
            print("starts at: ", event_result['start']['dateTime'])
            print("ends at: ", event_result['end']['dateTime'])

        return event_result

    def delete_event(self,
                     event_id,
                     calendar_id=None,
                     print_results=False
                     ):
        try:
            self.service.events().delete(
                calendarId=calendar_id if calendar_id else self.calendar_id,
                eventId=event_id,
            ).execute()
        except googleapiclient.errors.HttpError:
            print("Failed to delete event")

    def extract_event_info(self,
                           event
                           ):
        info = {}
        info['start_datetime'] = parser.parse(
            event['start'].get('dateTime', event['start'].get('date'))).\
            replace(tzinfo=None)
        info['end_datetime'] = parser.parse(
            event['end'].get('dateTime', event['end'].get('date'))).\
            replace(tzinfo=None)
        info['description'] = event.get('description', '')

        return info