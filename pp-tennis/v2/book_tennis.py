#!/usr/bin/env python3

from session import Session
from courts import Courts
import json

COURT_TYPES = ['Clay', 'Hard']

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
    parser.add_argument('--start_hour', type=int,
                        help='beginning of time range to book court (hour)')
    parser.add_argument('--end_hour', type=int,
                        help='end of time range to book court (hour)')
    parser.add_argument('--permitted', type=bool,
                        help='include courts requiring permit')

    args = parser.parse_args()

    session = Session(args.email, args.password).session
    for court_type in COURT_TYPES:
        print(args.court_date, court_type)
        print(
            json.dumps(
                Courts(
                    args.court_date,
                    args.start_hour,
                    args.end_hour,
                    court_type,
                    args.permitted,
                    session
                ).free_court_times,
                indent=4
            )
        )
