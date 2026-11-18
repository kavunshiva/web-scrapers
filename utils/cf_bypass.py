"""Browser-backed HTTP session for getting past Cloudflare's bot check.

Cloudflare's clearance cookie (`cf_clearance`) is bound to the browser's
fingerprint (user agent, TLS, IP), so handing it to `requests` usually fails.
Instead, every request here is made by a real Chromium instance via
Playwright: GETs are page navigations, POSTs are `fetch()` calls issued from
inside the page, so they carry the browser's cookies, UA and fingerprint.

A persistent browser profile is used so the clearance cookie survives between
cron runs and the challenge usually only has to be solved occasionally.

Setup:
    pip install playwright
    playwright install chromium
"""

import os
import time
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROFILE_DIR = os.path.join(CURRENT_DIR, '.cf_browser_profile')

# Titles Cloudflare uses for its interstitial/challenge pages.
CHALLENGE_TITLES = ('Just a moment', 'Attention Required', 'Please wait')

POST_JS = '''
async ({url, data, referrer}) => {
    const res = await fetch(url, {
        method: 'POST',
        body: new URLSearchParams(data),
        credentials: 'same-origin',
        redirect: 'follow',
        ...(referrer ? {referrer} : {}),
    });
    return {status: res.status, text: await res.text()};
}
'''


class CloudflareChallengeError(RuntimeError):
    pass


class CfResponse:
    """Minimal stand-in for `requests.Response`: `.text`, `.status_code`,
    and `.cookies` (a dict of the browser's cookies for the request URL)."""

    def __init__(self, text, status_code, cookies):
        self.text = text
        self.status_code = status_code
        self.cookies = cookies


class CfSession:
    """Use as a context manager so the browser is always shut down:

        with CfSession() as http:
            page = http.get('https://example.com/')
            res = http.post('https://example.com/form/', data={...})
    """

    def __init__(
        self,
        headless=False,
        profile_dir=DEFAULT_PROFILE_DIR,
        challenge_timeout=30,
    ):
        # Headless Chromium is much more likely to be challenged/blocked, so
        # headed is the default. Try headless=True and fall back if it fails.
        self.headless = headless
        self.profile_dir = profile_dir
        self.challenge_timeout = challenge_timeout

    def __enter__(self):
        self._pw = sync_playwright().start()
        self.context = self._pw.chromium.launch_persistent_context(
            self.profile_dir,
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled'],
        )
        self.page = (
            self.context.pages[0]
            if self.context.pages
            else self.context.new_page()
        )
        return self

    def __exit__(self, *exc):
        self.context.close()
        self._pw.stop()

    def get(self, url):
        res = self.page.goto(url, wait_until='domcontentloaded')
        challenged = self._wait_for_challenge()
        # If a challenge ran, the original response was the challenge page.
        status = 200 if challenged else (res.status if res else None)
        return CfResponse(self._settled_content(), status, self._cookies(url))

    def _settled_content(self, attempts=10):
        """page.content() raises if a navigation (redirect, Cloudflare's
        background check reloading the page) is in flight; wait it out."""
        for i in range(attempts):
            try:
                self.page.wait_for_load_state('load')
                return self.page.content()
            except PlaywrightError as e:
                if 'navigating' not in str(e) or i == attempts - 1:
                    raise
                self.page.wait_for_timeout(500)

    def post(self, url, data, referer=None):
        # fetch() must run from a page on the same origin to send its cookies.
        if urlparse(self.page.url).netloc != urlparse(url).netloc:
            self.get(referer or url)
        result = self.page.evaluate(
            POST_JS,
            {'url': url, 'data': data, 'referrer': referer},
        )
        return CfResponse(result['text'], result['status'], self._cookies(url))

    def _cookies(self, url):
        return {c['name']: c['value'] for c in self.context.cookies(url)}

    def _title(self):
        try:
            return self.page.title()
        except PlaywrightError:
            # Page is mid-navigation (e.g. challenge redirecting).
            return CHALLENGE_TITLES[0]

    def _wait_for_challenge(self):
        """Block until the Cloudflare interstitial clears. Returns whether a
        challenge was seen."""
        if not any(t in self._title() for t in CHALLENGE_TITLES):
            return False
        deadline = time.monotonic() + self.challenge_timeout
        while any(t in self._title() for t in CHALLENGE_TITLES):
            if time.monotonic() > deadline:
                raise CloudflareChallengeError(
                    f'Cloudflare challenge did not clear within '
                    f'{self.challenge_timeout}s at {self.page.url}'
                )
            self.page.wait_for_timeout(500)
        self.page.wait_for_load_state('domcontentloaded')
        return True
