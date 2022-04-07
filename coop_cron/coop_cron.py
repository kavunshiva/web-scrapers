from bs4 import BeautifulSoup as bs
from datetime import date, datetime
from os.path import exists
import subprocess
import json
import pprint
import re
import requests as r

class CoopCron:
    BASE_URL = 'https://members.foodcoop.com/services'

    CMD = '''
    on run argv
      display notification (item 2 of argv) with title (item 1 of argv)
    end run
    '''

    def __init__(self, username, password, target_shift={}):
        self.username = username
        self.password = password
        self.target_shift = target_shift
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

    def get_csrfmiddlewaretoken(self, page):
        return bs(page.text, 'html.parser').find(
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

    def get_shift_description(self, shift_id):
        return r.get(
            f'{self.BASE_URL}/shift_claim/{shift_id}/',
            headers={
                'cookie': \
                    f'csrftoken={self.csrftoken}; sessionid={self.sessionid}'
            }
        )

    def book_or_cancel_shift(self, shift_id, extra_data, confirmation_message):
        data = {
            'csrfmiddlewaretoken': self.get_csrfmiddlewaretoken(
                self.get_shift_description(shift_id)
            ),
            'shift_id': shift_id,
        }
        data.update(extra_data)

        res = r.post(
            f'{self.BASE_URL}/shift_claim/{shift_id}/',
            headers={
                'cookie': \
                    f'csrftoken={self.csrftoken}; sessionid={self.sessionid}',
                'Referer': f'{self.BASE_URL}/shift_claim/{shift_id}/',
            },
            data=data,
        )

        return True if re.search(confirmation_message, res.text) else False

    def book_shift(self, shift_id):
        return self.book_or_cancel_shift(
            shift_id,
            {'claim': 'Work this shift'},
            'You are now scheduled to work this shift.',
        )

    def cancel_shift(self, shift_id):
        return self.book_or_cancel_shift(
            shift_id,
            {'cancel': 'CANCEL SHIFT'},
            'You have cancelled your shift.',
        )

    def get_active_shift_count(self, shifts):
        count = 0
        for shift_details in shifts.values():
            if 'approx_time_deleted' not in shift_details:
                count += 1
        return count

    def delete_shifts_from_collection(self, shifts, new_shifts, ts):
        deleted_shift_count = 0
        for id, details in shifts.items():
            if id not in new_shifts and 'approx_time_deleted' not in details:
                details['approx_time_deleted'] = ts
                shifts[id] = details
                deleted_shift_count += 1
        return deleted_shift_count

    def add_shifts_to_collection(self, shifts, new_shifts, ts):
        real_new_shift_count = 0
        for id, details in new_shifts.items():
            if id not in shifts:
                details['approx_time_added'] = ts
                shifts[id] = details
                real_new_shift_count += 1
            if (
                (id not in shifts or 'booked' not in shifts[id]) and \
                self.target_shift and \
                self.target_shift['title'] == details['title'] and \
                re.search(
                    self.target_shift['date'],
                    details['shift_time'],
                ) and \
                self.book_shift(id)
            ):
                details['booked'] = True
                shifts[id] = details
                self.notify(
                    f"{details['title']} at {details['shift_time']}",
                    f"booked at {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}",
                )

        return real_new_shift_count

    def load_shifts_from_file(self, filename):
        if not exists(filename):
            with open(filename, 'w+') as f:
                f.write('{}')
        with open(filename, 'r') as f:
            shifts = json.loads(f.read())
        return shifts

    def write_shifts_to_file(self, filename):
        shifts = self.load_shifts_from_file(filename)
        new_shifts = self.get_shift_calendar()
        ts = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        deleted_shift_count = \
            self.delete_shifts_from_collection(shifts, new_shifts, ts)
        real_new_shift_count = \
            self.add_shifts_to_collection(shifts, new_shifts, ts)

        print(
            f'{real_new_shift_count} new shifts processed, ' \
            f'{deleted_shift_count} shifts deleted ' \
            f'({self.get_active_shift_count(shifts)} active shifts total) ' \
            f'at {ts}'
        )

        with open(filename, 'w') as f:
            f.write(json.dumps(shifts, indent=4))

    def notify(self, title, text):
        subprocess.call(['osascript', '-e', self.CMD, title, text])

if __name__ == '__main__':
    import argparse

    pp = pprint.PrettyPrinter(indent=4)

    parser = argparse.ArgumentParser(
        description='Get available shifts from the Park Slope Food Coop.'
    )
    parser.add_argument('--username', type=str,
                        help='coop account username')
    parser.add_argument('--password', type=str,
                        help='coop account password')
    parser.add_argument('--shift_title', type=str,
                        help='target shift name')
    parser.add_argument('--target_date', type=str,
                        help='target shift date')

    args = parser.parse_args()

    target_shift = {}

    if (args.shift_title and args.target_date):
        target_shift = {'title': args.shift_title, 'date': args.target_date}

    cc = CoopCron(args.username, args.password, target_shift)
    cc.write_shifts_to_file('shifts.json')
