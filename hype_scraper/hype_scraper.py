import argparse
import datetime
from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession
from bs4 import BeautifulSoup as bs

def get_date(soup):
    return datetime \
        .datetime \
        .strptime(soup.find('span', {'class': 'date'}).text, '%b %d, %Y') \
        .strftime('%Y-%m-%d')

def get_artists(soup):
    artists = []
    for track_name in soup.find_all('h3', {'class': 'track_name'}):
        artist = track_name.find('a', {'class': 'artist'})
        if artist:
            artists += artist
    return artists

def get_artists_from_stack(raw_stack, num):
    soup = bs(raw_stack.text, 'html.parser')
    date = get_date(soup)
    with open('artists2.tsv', 'a') as f:
        for artist in get_artists(soup):
            f.write(f'{num}\t{date}\t{artist}\n')

def fetched_sorted_stacks(stacks):
    stacks_by_num = {}
    for stack in as_completed(stacks):
        stacks_by_num[stack.num] = stack.result()
    return {k: stacks_by_num[k] for k in sorted(stacks_by_num)}.items()

def get_artists_from_stacks(start_num, end_num, auth):
    stack_requests = []
    session = FuturesSession()

    for num in range(start_num, end_num + 1):
        url = f'https://hypem.com/stack/{num}'
        stack_request = session.get(url, headers={'Cookie': f'AUTH={auth}'})
        stack_request.num = num
        stack_requests.append(stack_request)

    for num, raw_stack in fetched_sorted_stacks(stack_requests):
        get_artists_from_stack(raw_stack, num)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Get artists from Hype Machine.'
    )
    parser.add_argument('--first_stack', type=int,
                        help='the first stack from which to pull')
    parser.add_argument('--last_stack', type=int,
                        help='the last stack from which to pull')
    parser.add_argument('--auth', type=str,
                        help='the AUTH cookie for Hype Machine')

    args = parser.parse_args()

    get_artists_from_stacks(args.first_stack, args.last_stack, args.auth)
