import json

class CourtTime:
    BOOK_COURT_URL = 'https://prospectpark.aptussoft.com/Member/Aptus/CourtBooking_BookAppointment'
    DURATION = 60
    BOOKING_DETAILS = {
        'Duration': DURATION,
        'ItemCode': 'COURTONOUT',
        'Instructors': '',
        'Notes': '',
        'GuestAccts': '',
    }

    def __init__(self, id, name, date_str, start, end, booked=False):
        self.id = id
        self.name = name
        self.date_str = date_str
        self.start = start
        self.end = end
        self.booked = booked

    def book(self, session, account_id):
        # return json.loads(
        #     self.session.post(
        #         self.BOOK_COURT_URL,
        #         json={
        #             'Acctno': self.account_id,
        #             'EventsParame': json.dumps(self.booking_details),
        #             'locationid': 'Brooklyn',
        #             'MemItemNo': 'Adult'
        #         }
        #     ).json()
        # )
        res = session.post(
            self.BOOK_COURT_URL,
            json={
                'Acctno': account_id,
                'EventsParame': json.dumps(self.booking_details(account_id)),
                'locationid': 'Brooklyn',
                'MemItemNo': 'Adult'
            }
        )
        breakpoint()

    def booking_details(self, account_id):
        return {
            **self.BOOKING_DETAILS,
            'Resource': self.id,
            'Date': self.date_str,
            'Stime': self.start.strftime('%I:%M%p'),
            'Etime': self.end.strftime('%I:%M%p'),
            'Attendees': str(account_id),
        }
        # {
        #     "Date":"08/06/2025",
        #     "Stime":"09:00PM",
        #     "Etime":"10:00PM",
        #     "Resource":"Clay2",
        #     "Attendees":"5869",
        #     "ItemCode":"COURTONOUT",
        #     "Duration":"60",
        #     "Instructors":"",
        #     "Notes":"",
        #     "GuestAccts":""
        # }
