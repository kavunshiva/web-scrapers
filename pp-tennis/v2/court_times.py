import json
from datetime import datetime, date, time, timedelta
from court_time import CourtTime

class CourtTimes:
    COURTS_URL = 'https://prospectpark.aptussoft.com/Member/Aptus/CourtBooking_Get'
    START_OF_DAY = time(6)
    START_OF_EVENING = time(19)
    END_OF_DAY = time(23)
    DAYTIME_PERMIT_COURTS = {'Court 4b', 'Court 5b', 'Court 6b'}
    EVENING_COURTS = \
        {'Court 1a', 'Court 2a', 'Court 3a', 'Court 4a', 'Court 5a'}

    def __init__(self, court_date, start_time, end_time, court_type, session,
                 permitted=False):
        self.court_date = court_date
        self.start_time = start_time and \
            datetime.strptime(start_time, '%H:%M').time()
        self.end_time = end_time and \
            datetime.strptime(end_time, '%H:%M').time()
        self.court_type = court_type
        self.permitted = permitted
        self.booking_data = self.get_booking_data(session)
        self.courts_by_id = self.get_courts_by_id()

    def available(self):
        available = []
        for id in self.courts_by_id.keys():
            start = self.start_time or self.START_OF_DAY
            for booked_court_time in self.booked_court_times_by_id()[id]:
                self.add_available(id, start, booked_court_time.start,
                                   available)
                start = booked_court_time.end
            self.add_available(id, start, self.end_time or self.END_OF_DAY,
                               available)
        return available

    def booked_court_times_by_id(self):
        court_times = {}
        for court_time in self.sorted_booked():
            id = court_time['resourceId']
            if id not in court_times:
                court_times[id] = []
            start = datetime.fromisoformat(court_time['start']).time()
            end = datetime.fromisoformat(court_time['end']).time()
            court_times[id].append(
                CourtTime(id=id, name=self.courts_by_id[id],
                          date_str=self.court_date, start=start, end=end,
                          booked=True)
            )
        return court_times

    def add_available(self, id, start, duration_end, available):
        while self.bookable_duration(start, duration_end):
            end = self.court_end_time(start)
            name = self.courts_by_id[id]
            if self.court_bookable(name, start, end):
                available.append(
                    CourtTime(id=id, name=name, date_str=self.court_date,
                                start=start, end=end)
                )
            start = end

    def bookable_duration(self, start, end):
        return self.time_difference_mins(start, end) >= CourtTime.DURATION

    def court_end_time(self, start):
        return (
            datetime.combine(date.min, start) +
            timedelta(minutes=CourtTime.DURATION)
        ).time()

    def court_bookable(self, name, start, end):
        if (self.start_time and start < self.start_time) or \
            (self.end_time and end > self.end_time):
            return False
        if start < self.START_OF_EVENING:
            return self.permitted and name in self.DAYTIME_PERMIT_COURTS
        return name in self.EVENING_COURTS

    def sorted_booked(self):
        return sorted(self.booking_data[1], key=lambda x : x['start'])

    def get_booking_data(self, session):
        return json.loads(
                session.post(
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

    def time_difference_mins(self, start, end):
        return (
            datetime.combine(date.min, end) - datetime.combine(date.min, start)
        ).total_seconds() / 60
