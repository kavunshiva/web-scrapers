import json
from datetime import datetime

class Courts:
    COURTS_URL = 'https://prospectpark.aptussoft.com/Member/Aptus/CourtBooking_Get'
    HOURS = set(range(6,23))
    COURT_HOUR_TIMES = {hour:set() for hour in HOURS}
    DAYTIME_PERMIT_COURTS = {'Court 4b', 'Court 5b', 'Court 6b'}
    EVENING_COURTS = \
        {'Court 1a', 'Court 2a', 'Court 3a', 'Court 4a', 'Court 5a'}

    def __init__(self, court_date, court_type, session):
        self.court_date = court_date
        self.court_type = court_type
        self.session = session
        self.booking_data = self.get_booking_data()
        self.courts_by_id = self.get_courts_by_id()
        self.booked_court_times = self.get_booked_court_times()
        self.free_court_times = self.get_free_court_times()

    def get_booking_data(self):
        return json.loads(
                self.session.post(
                self.COURTS_URL,
                json={
                    'locationId': 'Brooklyn',
                    'resourcetype': self.court_type,
                    'start': self.court_date,
                    'end': self.court_date,
                }
            ).json()['CourtBooking_GetResult']
        )

    def get_courts_by_id(self):
        courts_by_id = {}
        for court in self.booking_data[0]:
            courts_by_id[court['id']] = court['name']
        return courts_by_id

    def get_booked_court_times(self):
        for time_slot in self.booking_data[1]:
            start_hour = datetime.fromisoformat(time_slot['start']).hour
            end_hour = datetime.fromisoformat(time_slot['end']).hour
            court_id = time_slot['resourceId']
            for hour in range(start_hour, end_hour):
                self.COURT_HOUR_TIMES[hour].add(court_id)
        booked_court_times = {}
        for hour, court_ids in self.COURT_HOUR_TIMES.items():
            booked_court_times[hour] = list(court_ids)
        return booked_court_times

    def get_free_court_times(self):
        free_court_times = {}
        for hour, court_ids in self.COURT_HOUR_TIMES.items():
            court_names = []
            for court_id in self.bookable_courts(hour) - court_ids:
                court_names.append(self.courts_by_id[court_id])
            if court_names:
                free_court_times[hour] = court_names
        return free_court_times
    
    def bookable_courts(self, hour):
        bookable_courts = set()
        for court_id, court_name in self.courts_by_id.items():
            if self.court_bookable(hour, court_name):
                bookable_courts.add(court_id)
        return bookable_courts

    def court_bookable(self, hour, court_name):
        if hour < 19:
            return court_name in self.DAYTIME_PERMIT_COURTS
        return court_name in self.EVENING_COURTS
