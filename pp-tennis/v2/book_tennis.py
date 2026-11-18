#!/usr/bin/env python3

from session import Session
from court_times import CourtTimes
import sys
import json
sys.path.append('../../utils/gmailer/')
from gmailer import GMailer

COURT_TYPES = ['Clay', 'Hard']
REPORTED_FREE_COURTS_FILE = 'court_times.json'

def notify(title, text, recipient_emails):
    try:
        mailer = GMailer()
        mailer.send_message(
            'me',
            mailer.create_message( 'me', recipient_emails, title, text)
        )
    except Exception as error:
        print(error)

def record_court_times():
    previously_unreported_free_courts = []
    with open(REPORTED_FREE_COURTS_FILE, 'a+') as f:
        f.seek(0)
        notified_court_times = json.loads(f.read() or '{}')
    for court_time in sorted(available_court_times, key=lambda x : x.name):
        free_court_message = previously_unreported_free_court_message(
            court_time,
            notified_court_times
        )
        if free_court_message:
            previously_unreported_free_courts.append(free_court_message)
    with open('court_times.json', 'w+') as f:
        f.write(json.dumps(notified_court_times, indent=4))
    return previously_unreported_free_courts

def previously_unreported_free_court_message(court_time, notified_court_times):
    formatted_start_time = court_time.start.strftime('%I:%M%p')
    if args.court_date not in notified_court_times:
        notified_court_times[args.court_date] = {}
    if formatted_start_time not in notified_court_times[args.court_date]:
        notified_court_times[args.court_date][formatted_start_time] = []
    if court_time.id not in notified_court_times[args.court_date][formatted_start_time]:
        notified_court_times[args.court_date][formatted_start_time].append(court_time.id)
        return f"     {formatted_start_time}: {court_time.name}"

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description=\
            'Get available court times from the Prospect Park Tennis Center.'
    )
    parser.add_argument('--email', type=str,
                        help='tennis center account email')
    parser.add_argument('--password', type=str,
                        help='tennis center account email')
    parser.add_argument('--court_date', type=str,
                        help='date to book court (formatted: MM/DD/YYYY)')
    parser.add_argument('--start_time', type=str,
                        help='beginning of time range to book court (HH:MM)')
    parser.add_argument('--end_time', type=str,
                        help='end of time range to book court (HH:MM)')
    parser.add_argument('--recipient_emails', type=str,
                        help='emails to notify of open courts '\
                             '(as a comma-separated list)')
    parser.add_argument('--permitted', type=bool,
                        help='include courts requiring permit')

    args = parser.parse_args()

    session = Session(args.email, args.password).session
    available_court_times = []
    for court_type in COURT_TYPES:
        for court_time in CourtTimes(args.court_date, args.start_time,
                                     args.end_time, court_type, session,
                                     args.permitted).available():
            available_court_times.append(court_time)
    court_time_messages = record_court_times(available_court_times) or []
    if court_time_messages:
        message_lines = [
            f'The following courts are available for {args.court_date}:\n'
        ]
        message_lines += court_time_messages
        message_lines.append('\nbook \'em while you still can!')
        message = '\n'.join(message_lines)
        if args.recipient_emails:
            notify(f'TENNIS COURTS AVAILABLE - {args.court_date}', message,
                   args.recipient_emails)
        print(message)
    else:
        print(f'No courts are available for {args.court_date}')
