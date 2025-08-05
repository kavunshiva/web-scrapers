#!/usr/bin/env python3

from session import Session
from court_times import CourtTimes
import sys
sys.path.append('../../utils/gmailer/')
from gmailer import GMailer

COURT_TYPES = ['Clay', 'Hard']

def notify(title, text, recipient_emails):
    try:
        mailer = GMailer()
        mailer.send_message(
            'me',
            mailer.create_message( 'me', recipient_emails, title, text)
        )
    except Exception as error:
        print(error)

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
    if len(available_court_times):
        message_lines = [
            f'The following courts are available for {args.court_date}:\n'
        ]
        for court_time in sorted(available_court_times, key=lambda x : x.name):
            message_lines.append(
                f"     {court_time.start.strftime('%I:%M%p')}: " \
                    f'{court_time.name}'
            )
        message_lines.append('\nbook \'em while you still can!')
        message = '\n'.join(message_lines)
        if args.recipient_emails:
            notify(f'TENNIS COURTS AVAILABLE - {args.court_date}', message,
                   args.recipient_emails)
        print(message)
    else:
        print(f'No courts are available for {args.court_date}')
