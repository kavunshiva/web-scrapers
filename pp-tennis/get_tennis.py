#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from datetime import datetime
import pytz
import json
import sys
sys.path.append('../utils/gmailer/')
from gmailer import GMailer


options = Options()
options.add_argument('--headless')
# service definition w/ executable_path not necessary on all systems
service = Service(executable_path='/usr/lib/chromium-browser/chromedriver')
driver = webdriver.Chrome(
    service=service,
    options=options
)
court_times = set()


def check_if_too_soon(court_time):
    days_till = (
        pytz.timezone('US/Eastern').localize(court_time).date() -
        datetime.now(pytz.timezone('US/Eastern')).date()
    ).days
    logged_court_time = f'[{datetime.now()}] court time {court_time} ET'
    if days_till < 0:
        sys.exit(f'{logged_court_time} in past. exiting.')
    elif days_till == 1:
        sys.exit(f'{logged_court_time} too soon (<1 day away). exiting.')
    elif days_till > 7:
        sys.exit(f'{logged_court_time} too far away (>1 week away). exiting.')


def find_and_click_button(button_identifier, identifier_type, wait=False):
    indentifier = (identifier_type, button_identifier)
    if wait:
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(indentifier)
        )
    else:
        button = driver.find_element(*indentifier)
    if button:
        try:
            button.click()
        except:
            raise Exception((
                f'button with {identifier_type} {button_identifier} '
                'not clickable'
            ))
    else:
        raise Exception(
            f'could not find button {button_identifier} by {identifier_type}'
        )


def find_login_element(type):
    return driver.find_element(
        By.ID,
        f'ctl00_pageContentHolder_loginControl_{type}',
    )


def login(username, password):
    driver.get('https://hnd-p-ols.spectrumng.net/prospectpark/Login.aspx')
    find_login_element('UserName').send_keys(username)
    find_login_element('Password').send_keys(password)
    find_login_element('Login').click()


def navigate_to_scheduler():
    find_and_click_button('menu_SCH', By.ID, True) # book courts
    find_and_click_button('divContainer', By.ID, True) # court reservations
    find_and_click_button('divContainer', By.ID, True) # online ind. court res.


def select_court_time(desired_court_time):
    find_and_click_button('ui-datepicker-trigger', By.CLASS_NAME)
    Select(
        driver.find_element(By.CLASS_NAME, 'ui-datepicker-year')
    ).select_by_value(str(desired_court_time.year))
    Select(
        driver.find_element(By.CLASS_NAME, 'ui-datepicker-month')
    ).select_by_value(str(desired_court_time.month - 1))
    find_and_click_button(
        (
            '//table[@class="ui-datepicker-calendar"]/tbody/tr/td/'
            f'a[text() = "{desired_court_time.day}"]'
        ),
        By.XPATH,
    )
    find_and_click_button('btnContinue', By.ID)


def get_availabile_court_time(desired_court_time):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                '//div[@id="schPageData"]/div',
            ))
        )
        return driver.find_element(
            By.XPATH,
            (
                '//table[@class="SmallTableBorder tblSchslots"]/'
                'tbody/tr[@class="DgText"]/'\
                f'td[1][text() = "{desired_court_time.strftime("%I:%M %p")}"]'
            ),
        )
    except:
        print(f'[{datetime.now()}] no court available at {desired_court_time}')
        return None


def add_court_to_cart(available_court_time):
    available_court_time.find_element(
        By.XPATH,
        'parent::tr/td/a[contains(@class, "schTblButton")]',
    ).click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.XPATH,
            '//span[@id="litFees"][text()!=" ...Loading"]',
        ))
    )

    find_and_click_button('btnContinue', By.ID)
    find_and_click_button('btnAcceptWaiver', By.ID)


def select_host_and_proceed_to_last_step():
    find_and_click_button(
        (
            '//table'
            '[@id='
                '"ctl00_'
                'pageContentHolder_'
                'ctrlAddSchedulerMember_'
                'ctrlMemberBuddy_gridViewMembers"'
            ']/tbody/tr[contains(@class, "DgText")][1]/'
            'td/span/input[@type="radio"]/parent::*'
        ),
        By.XPATH,
        True,
    ) # first host button
    find_and_click_button('ctl00_pageContentHolder_btnContinueCart', By.ID)
    find_and_click_button('ctl00_pageContentHolder_btnCancel', By.ID, True)


def purchase_court_time(notify_email=None):
    notify_email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.ID,
            'ctl00_pageContentHolder_confirmationControl_txtEmailAddr',
        ))
    )
    if notify_email:
        notify_email_field.send_keys(notify_email)

    submit_buttons = driver.find_elements(
        By.ID,
        'ctl00_pageContentHolder_btnSubmit',
    )
    if submit_buttons:
        print('[{datetime.now()}] found the submit button...')
        print('[{datetime.now()}] ...clicking it')
        submit_buttons[0].click() # enable to actually book

        with open('config.json', 'r') as f:
            creds = json.load(f)
            creds['shouldBook'] = False
        with open('config.json', 'w') as f:
            f.write(json.dumps(creds, indent=4))


def notify_me(court_time):
    try:
        mailer = GMailer()
        mailer.send_message(
            'me',
            mailer.create_message(
                'me',
                'kavunshiva@gmail.com',
                f'Tennis court booked: {court_time}',
                'Have fun kiddos.',
            )
        )
    except Exception as error:
        print(f'[{datetime.now()}] {error}')


def book_court(available_court_time, notify_email=None):
    add_court_to_cart(available_court_time)
    select_host_and_proceed_to_last_step()
    purchase_court_time(notify_email)


def get_availabilities(desired_court_time, notify_email=None):
    navigate_to_scheduler()
    select_court_time(desired_court_time)
    available_court_time = get_availabile_court_time(desired_court_time)
    if available_court_time:
        book_court(available_court_time, notify_email)
        notify_me(desired_court_time)


if __name__ == '__main__':
    import argparse
    from getpass import getpass

    start = datetime.now()

    parser = argparse.ArgumentParser(
        description='Book a court at the Prospect Park Tennis Center.'
    )
    parser.add_argument(
        '--court_time',
        type=str,
        help=(
            'the date and time (ISO) you\'d like to book (in US Eastern time), '
            'e.g., 2022-12-15T08:00'
        ),
    )
    parser.add_argument(
        '--notify_email',
        type=str,
        help='any additional emails to notify on successful booking',
    )

    args = parser.parse_args()
    court_time = datetime.fromisoformat(args.court_time)
    check_if_too_soon(court_time)

    # username = input('Enter Prospect Park Tennis Center username: ')
    # password = getpass(
    #     prompt='Enter Prospect Park Tennis Center password: '
    # )

    with open('config.json', 'r') as f:
        creds = json.load(f)
        username = creds['username']
        password = creds['password']
        should_book = creds['shouldBook']

    if not should_book:
        sys.exit(f'[{datetime.now()}] already booked a session. exiting.')

    login(username, password)
    get_availabilities(
        court_time,
        args.notify_email,
    )
    elapsed = datetime.now() - start
    print((
        f'[{datetime.now()}] '
        f'this took {elapsed.seconds}.{elapsed.microseconds} seconds to run'
    ))
