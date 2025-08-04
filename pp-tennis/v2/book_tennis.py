#!/usr/bin/env python3

from session import Session
from court_times import CourtTimes

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
    parser.add_argument('--start_time', type=str,
                        help='beginning of time range to book court (HH:MM)')
    parser.add_argument('--end_time', type=str,
                        help='end of time range to book court (HH:MM)')
    parser.add_argument('--permitted', type=bool,
                        help='include courts requiring permit')

    args = parser.parse_args()

    session = Session(args.email, args.password).session
    for court_type in COURT_TYPES:
        print(args.court_date, court_type)
        # print(
        #     json.dumps(
        #         Courts(
        #             args.court_date,
        #             args.start_time,
        #             args.end_time,
        #             court_type,
        #             args.permitted,
        #             session
        #         ).free_court_times,
        #         indent=4
        #     )
        # )
        free_court_times = CourtTimes(
            args.court_date,
            args.start_time,
            args.end_time,
            court_type,
            session,
            args.permitted,
        ).available()
        [print(court.id, court.name, court.start, court.end) for court in free_court_times]
        # ).free_court_times
        # should_book = True
        # for start_time, court_ids in free_court_times.items():
        #     for court_id in court_ids:
        #         if should_book:
        #             Court(court_id, args.court_date, start_time,
        #                   start_time + 1, 5869, session).book()
        #             should_book = False
        # print(
        #     json.dumps(
        #         Court(
        #             'Hard1',
        #             '08/06/2025',
        #             22,
        #             23,
        #             5869,
        #             session
        #         ).book(),
        #         indent=4
        #     )
        # )
