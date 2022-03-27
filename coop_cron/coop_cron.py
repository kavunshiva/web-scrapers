from bs4 import BeautifulSoup as bs
from datetime import date, datetime
from os.path import exists
import json
import pprint
import re
import requests as r

class CoopCron:
    BASE_URL = 'https://members.foodcoop.com/services'

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.csrftoken, self.sessionid = self.login()

    def get_sessionid(self, csrftoken, csrfmiddlewaretoken):
        return r.post(
            f'{self.BASE_URL}/login/',
            headers={
                'Referer': f'{self.BASE_URL}/login/',
                'Cookie': f'csrftoken={csrftoken}',
            },
            data={
                'username': self.username,
                'password': self.password,
                'csrfmiddlewaretoken': csrfmiddlewaretoken,
            },
        ).cookies.get('sessionid')

    def get_csrfmiddlewaretoken(self, login_page):
        return bs(login_page.text, 'html.parser').find(
            'input',
            {'name': 'csrfmiddlewaretoken'},
        )['value']

    def login(self):
        login_page = r.get(f'{self.BASE_URL}/login/')
        csrftoken = login_page.cookies.get('csrftoken')
        sessionid = self.get_sessionid(
            csrftoken,
            self.get_csrfmiddlewaretoken(login_page),
        )
        return (csrftoken, sessionid)

    def get_details(self, shift, date_str):
        id = re.search('\d+', shift['href']).group(0)
        texts = [t.strip() for t in shift.text.split('\n')]
        title = re.search('(\w+\s)+', texts[5] or texts[3]).group(0).strip()
        shift_time = datetime.strptime(
            f'{date_str} {shift.findChildren("b")[0].text}',
            '%Y-%m-%d %I:%M%p',
        ).isoformat()
        return (id, {'title': title, 'shift_time': shift_time})

    def get_formatted_date(self, day):
        raw_date = day.findChildren('p') and day.findChildren('p')[0].text
        if raw_date:
            data = [n.zfill(2) for n in re.findall('\d+', raw_date)]
            if not len(data) == 3:
                return None
            month, day, year = data
            return '-'.join([year, month, day])
        else:
            return None

    def parse_shifts(self, days):
        shifts = {}
        for day in days:
            date_str = self.get_formatted_date(day)
            if not date_str:
                continue
            raw_shifts = day.findChildren('a', { 'class': 'shift' })
            for shift in raw_shifts:
                id, details = self.get_details(shift, date_str)
                shifts[id] = details
        return shifts

    def get_shift_calendar(self):
        date_str = date.today().strftime('%Y-%m-%d')
        raw_cal = r.get(
            f'{self.BASE_URL}/shifts/0/0/0/{date_str}',
            headers={
                'cookie': \
                    f'csrftoken={self.csrftoken}; sessionid={self.sessionid}'
            }
        )
        days = bs(raw_cal.text, 'html.parser') \
                   .find_all('div', { 'class': 'col' })
        return self.parse_shifts(days)

    def write_shifts_to_file(self, filename):
        if not exists(filename):
            with open(filename, 'w+') as f:
                f.write('{}')
        with open(filename, 'r') as f:
            shifts = json.loads(f.read())

        new_shifts = self.get_shift_calendar()

        current_time_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        for id, details in shifts.items():
            if id not in new_shifts:
                details['approx_time_deleted'] = current_time_str
                shifts[id] = details

        real_new_shift_count = 0
        for id, details in new_shifts.items():
            if id not in shifts:
                details['approx_time_added'] = current_time_str
                shifts[id] = details
                real_new_shift_count += 1

        print(
            f'{real_new_shift_count} new shifts ' \
            f'processed at {current_time_str}\n'
        )

        with open(filename, 'w') as f:
            f.write(json.dumps(shifts, indent=4))

if __name__ == '__main__':
    import argparse

    pp = pprint.PrettyPrinter(indent=4)

    parser = argparse.ArgumentParser(
        description='Get artists from Hype Machine.'
    )
    parser.add_argument('--username', type=str,
                        help='coop account username')
    parser.add_argument('--password', type=str,
                        help='coop account password')

    args = parser.parse_args()

    cc = CoopCron(args.username, args.password)
    cc.write_shifts_to_file('shifts.json')
