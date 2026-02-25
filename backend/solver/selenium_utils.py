"""
Selenium automation module for LeetCode.

This module handles:
1. Manual login — opens Chrome for the user to log in, saves session cookies
2. Scraping problem title and description (via GraphQL API, no browser needed)
3. Submitting code to LeetCode using saved session cookies
4. Capturing the submission result

Uses Chrome WebDriver. Make sure chromedriver is installed.
"""

import os
import re
import html
import time
import json
import requests
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# How long to wait for elements to appear (seconds)
WAIT_TIMEOUT = 20

# Path to persist LeetCode session cookies between requests
BASE_DIR = Path(__file__).resolve().parent.parent
COOKIES_FILE = BASE_DIR / 'leetcode_cookies.json'

# How long to wait for the user to log in manually (seconds)
LOGIN_WAIT_TIMEOUT = 180


def get_chrome_driver(headless=False):
    """
    Create and return an undetected Chrome WebDriver instance.
    Uses undetected_chromedriver to bypass Cloudflare bot detection.
    """
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # undetected_chromedriver automatically patches Chrome to avoid bot detection
    driver = uc.Chrome(options=options, use_subprocess=True)
    return driver


# ── Cookie helpers ────────────────────────────────────────────────────────────

def save_cookies(driver):
    """Save all browser cookies from the current session to a JSON file."""
    cookies = driver.get_cookies()
    with open(COOKIES_FILE, 'w') as f:
        json.dump(cookies, f)
    print(f"[Cookies] Saved {len(cookies)} cookies to {COOKIES_FILE}")


def load_cookies(driver):
    """
    Load previously saved cookies into the driver.
    The driver must already be on a leetcode.com page before calling this.
    Returns True if cookies were loaded, False if no cookie file found.
    """
    if not COOKIES_FILE.exists():
        print("[Cookies] No saved cookies found.")
        return False
    with open(COOKIES_FILE, 'r') as f:
        cookies = json.load(f)
    for cookie in cookies:
        # Remove keys that Selenium doesn't accept
        cookie.pop('sameSite', None)
        cookie.pop('expiry', None)
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass
    print(f"[Cookies] Loaded {len(cookies)} cookies.")
    return True


def check_login_status():
    """
    Check whether saved LeetCode session cookies exist.
    Returns True if cookie file exists and contains a session cookie.
    """
    if not COOKIES_FILE.exists():
        return False
    try:
        with open(COOKIES_FILE, 'r') as f:
            cookies = json.load(f)
        # LeetCode uses LEETCODE_SESSION cookie for authentication
        session_cookies = [c for c in cookies if c.get('name') in ('LEETCODE_SESSION', 'csrftoken')]
        return len(session_cookies) >= 1
    except Exception:
        return False


def clear_cookies():
    """Delete saved cookies (force the user to log in again)."""
    if COOKIES_FILE.exists():
        COOKIES_FILE.unlink()
        print("[Cookies] Cleared saved cookies.")


def open_browser_for_login():
    """
    Open a visible Chrome browser window on the LeetCode login page.
    Wait up to LOGIN_WAIT_TIMEOUT seconds for the user to complete login manually.
    On success, save cookies and return {'success': True}.
    On timeout, return {'success': False, 'error': '...'}.
    """
    driver = get_chrome_driver(headless=False)
    try:
        print("[Login] Opening LeetCode login page for manual login...")
        driver.get('https://leetcode.com/accounts/login/')

        # Maximise window so the user can see the form clearly
        driver.maximize_window()

        print(f"[Login] Waiting up to {LOGIN_WAIT_TIMEOUT}s for user to log in...")

        # Poll until we are redirected away from the login page
        deadline = time.time() + LOGIN_WAIT_TIMEOUT
        logged_in = False
        while time.time() < deadline:
            current_url = driver.current_url
            # LeetCode redirects to /problemset/ or / after a successful login
            if 'accounts/login' not in current_url and 'leetcode.com' in current_url:
                logged_in = True
                break
            time.sleep(1)

        if not logged_in:
            driver.quit()
            return {'success': False, 'error': 'Login timed out. Please try again.'}

        # Give the page a moment to set all session cookies
        time.sleep(2)
        save_cookies(driver)
        print("[Login] User logged in successfully. Cookies saved.")
        driver.quit()
        return {'success': True}

    except Exception as e:
        print(f"[Login] Error during manual login: {e}")
        try:
            driver.quit()
        except Exception:
            pass
        return {'success': False, 'error': str(e)}


# ── LeetCode GraphQL constants ───────────────────────────────────────────────
GRAPHQL_URL = 'https://leetcode.com/graphql'
GRAPHQL_HEADERS = {
    'Content-Type': 'application/json',
    'Referer': 'https://leetcode.com/problemset/',
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
}


def scrape_problem(problem_number):
    """
    Fetch LeetCode problem title and description via the public GraphQL API.
    No browser or login required for reading public problem data.

    Args:
        problem_number (int): The LeetCode problem number (e.g., 1 for Two Sum)

    Returns:
        dict with keys: title, description
        Returns None if the request fails.
    """

    # ── Step 1: Resolve problem number → URL slug ─────────────────────────
    list_query = """
    query problemsetQuestionList($skip: Int, $limit: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(
        categorySlug: ""
        limit: $limit
        skip: $skip
        filters: $filters
      ) {
        questions: data {
          frontendQuestionId: questionFrontendId
          titleSlug
          title
        }
      }
    }
    """
    try:
        r = requests.post(
            GRAPHQL_URL,
            json={
                'query': list_query,
                'variables': {
                    'skip': problem_number - 1,
                    'limit': 1,
                    'filters': {},
                },
            },
            headers=GRAPHQL_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        questions = (
            r.json()
            .get('data', {})
            .get('problemsetQuestionList', {})
            .get('questions', [])
        )
        if not questions:
            print(f'[API] Problem #{problem_number} not found in problem list.')
            return None
        title_slug = questions[0]['titleSlug']
        print(f'[API] Resolved slug for #{problem_number}: {title_slug}')
    except Exception as e:
        print(f'[API] Failed to get problem slug: {e}')
        return None

    # ── Step 2: Fetch full problem details ────────────────────────────────
    detail_query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionFrontendId
        title
        content
        difficulty
      }
    }
    """
    try:
        r = requests.post(
            GRAPHQL_URL,
            json={'query': detail_query, 'variables': {'titleSlug': title_slug}},
            headers=GRAPHQL_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        question = r.json().get('data', {}).get('question')
        if not question or not question.get('content'):
            print(f'[API] No content returned for {title_slug}.')
            return None

        # Strip HTML tags → plain text description
        raw_html = question['content']
        clean_text = re.sub(r'<[^>]+>', '', html.unescape(raw_html))
        clean_text = clean_text.replace('\xa0', ' ')          # non-breaking spaces
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()

        print(f"[API] Title: {question['title']}")
        print(f'[API] Description: {len(clean_text)} chars')
        return {
            'title': question['title'],
            'description': clean_text,
        }
    except Exception as e:
        print(f'[API] Failed to fetch problem details: {e}')
        return None


def _get_problem_slug(problem_number):
    """
    Resolve a problem number to its LeetCode URL slug via GraphQL.
    Returns the slug string, or None on failure.
    """
    list_query = """
    query problemsetQuestionList($skip: Int, $limit: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(
        categorySlug: ""
        limit: $limit
        skip: $skip
        filters: $filters
      ) {
        questions: data {
          frontendQuestionId: questionFrontendId
          titleSlug
        }
      }
    }
    """
    try:
        r = requests.post(
            GRAPHQL_URL,
            json={'query': list_query, 'variables': {'skip': problem_number - 1, 'limit': 1, 'filters': {}}},
            headers=GRAPHQL_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        questions = r.json().get('data', {}).get('problemsetQuestionList', {}).get('questions', [])
        if questions:
            return questions[0]['titleSlug']
    except Exception as e:
        print(f'[API] Failed to get slug: {e}')
    return None


def _get_question_id(slug):
    """
    Fetch the internal numeric question ID for a given problem slug via GraphQL.
    This is required by the submission API.
    Returns the question ID string, or None on failure.
    """
    query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
      }
    }
    """
    try:
        r = requests.post(
            GRAPHQL_URL,
            json={'query': query, 'variables': {'titleSlug': slug}},
            headers=GRAPHQL_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get('data', {}).get('question', {}).get('questionId')
    except Exception as e:
        print(f'[API] Failed to get question ID: {e}')
    return None


def submit_solution(problem_number, code):
    """
    Submit a Python3 solution to LeetCode using saved session cookies.

    Uses LeetCode's HTTP submission API directly — no browser needed.
    This guarantees the language is always set to python3.

    Args:
        problem_number (int): LeetCode problem number
        code (str): Python solution code to submit

    Returns:
        str: submission status — 'Accepted', 'Wrong Answer', 'Time Limit Exceeded', or 'Error: ...'
    """
    if not check_login_status():
        return 'Error: Not logged in. Please log in first.'

    # ── Step 1: Resolve slug and question ID ─────────────────────────────
    slug = _get_problem_slug(problem_number)
    if not slug:
        return 'Error: Could not resolve problem slug.'

    question_id = _get_question_id(slug)
    if not question_id:
        return 'Error: Could not resolve question ID.'

    # ── Step 2: Load saved cookies into a requests Session ───────────────
    if not COOKIES_FILE.exists():
        return 'Error: No saved cookies. Please log in first.'

    with open(COOKIES_FILE, 'r') as f:
        raw_cookies = json.load(f)

    session = requests.Session()
    csrf_token = None
    for c in raw_cookies:
        session.cookies.set(c['name'], c['value'], domain=c.get('domain', 'leetcode.com'))
        if c['name'] == 'csrftoken':
            csrf_token = c['value']

    if not csrf_token:
        return 'Error: csrftoken not found in saved cookies. Please log in again.'

    # ── Step 3: POST to LeetCode submission endpoint ──────────────────────
    submit_url = f'https://leetcode.com/problems/{slug}/submit/'
    headers = {
        'Content-Type': 'application/json',
        'Referer': f'https://leetcode.com/problems/{slug}/',
        'X-CSRFToken': csrf_token,
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Origin': 'https://leetcode.com',
    }
    payload = {
        'lang': 'python3',        # Always Python3 — no UI interaction needed
        'question_id': question_id,
        'typed_code': code,
    }

    print(f'[Submit] Submitting problem #{problem_number} ({slug}) as python3...')
    try:
        resp = session.post(submit_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        submission_id = resp.json().get('submission_id')
        if not submission_id:
            return 'Error: No submission_id returned from LeetCode.'
        print(f'[Submit] Got submission_id: {submission_id}')
    except Exception as e:
        print(f'[Submit] Submission request failed: {e}')
        return f'Error: Submission failed — {e}'

    # ── Step 4: Poll for the result ───────────────────────────────────────
    check_url = f'https://leetcode.com/submissions/detail/{submission_id}/check/'
    print('[Submit] Polling for result...')
    for attempt in range(30):   # poll up to ~60 seconds
        time.sleep(2)
        try:
            check_resp = session.get(check_url, headers=headers, timeout=15)
            check_resp.raise_for_status()
            data = check_resp.json()
            state = data.get('state', '')
            print(f'[Submit] Poll #{attempt + 1}: state={state}')
            if state == 'SUCCESS':
                status_code = data.get('status_msg', '')
                print(f'[Submit] Final result: {status_code}')
                return status_code   # e.g. 'Accepted', 'Wrong Answer', etc.
            elif state in ('PENDING', 'STARTED', 'PROCESSING'):
                continue   # still running
            else:
                return f'Error: Unexpected state — {state}'
        except Exception as e:
            print(f'[Submit] Polling error: {e}')
            return f'Error: Polling failed — {e}'

    return 'Error: Timeout waiting for submission result.'


# ── Legacy Selenium submission (kept for reference, no longer used) ───────────
def _submit_solution_selenium(problem_number, code):
    """Selenium-based submission — replaced by API-based submit_solution above."""
    slug = _get_problem_slug(problem_number)
    if not slug:
        return 'Error: Could not resolve problem slug.'

    driver = get_chrome_driver(headless=False)

    try:
        print("[Selenium] Loading session cookies...")
        driver.get('https://leetcode.com/')
        time.sleep(2)
        load_cookies(driver)
        driver.get('https://leetcode.com/')
        time.sleep(3)

        if 'accounts/login' in driver.current_url:
            clear_cookies()
            driver.quit()
            return 'Error: Session expired. Please log in again.'

        problem_url = f'https://leetcode.com/problems/{slug}/'
        print(f"[Selenium] Navigating to {problem_url}")
        driver.get(problem_url)
        time.sleep(5)

        wait = WebDriverWait(driver, WAIT_TIMEOUT)

        # Language selection (unreliable — replaced by API approach)
        print("[Selenium] Setting language to Python3...")
        try:
            lang_btn = None
            for selector in [
                'button[id*="headlessui-listbox-button"]',
                'button[data-cy*="lang"]',
                'button[id*="lang"]',
            ]:
                try:
                    lang_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue

            if lang_btn and 'Python' not in lang_btn.text:
                lang_btn.click()
                time.sleep(1)
                python_option = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[contains(text(),"Python3") or contains(text(),"python3")]')
                ))
                python_option.click()
                time.sleep(2)
        except Exception as e:
            print(f"[Selenium] Language selection skipped: {e}")

        # ── Step 4: Inject code into Monaco editor ────────────────────────
        print("[Selenium] Injecting code into editor...")
        time.sleep(2)

        injected = False

        # Try Monaco editor first (LeetCode's current editor)
        try:
            driver.execute_script("""
                var editors = monaco.editor.getEditors();
                if (editors && editors.length > 0) {
                    var model = editors[0].getModel();
                    if (model) {
                        model.setValue(arguments[0]);
                    }
                }
            """, code)
            time.sleep(1)
            # Verify injection by reading back the value
            current_val = driver.execute_script("""
                var editors = monaco.editor.getEditors();
                if (editors && editors.length > 0) {
                    return editors[0].getValue();
                }
                return '';
            """)
            if current_val and len(current_val.strip()) > 10:
                injected = True
                print("[Selenium] Code injected via Monaco editor.")
        except Exception as e:
            print(f"[Selenium] Monaco injection failed: {e}")

        # Fallback: CodeMirror (older LeetCode)
        if not injected:
            try:
                driver.execute_script("""
                    var cm = document.querySelector('.CodeMirror');
                    if (cm && cm.CodeMirror) {
                        cm.CodeMirror.setValue(arguments[0]);
                    }
                """, code)
                time.sleep(1)
                injected = True
                print("[Selenium] Code injected via CodeMirror.")
            except Exception as e:
                print(f"[Selenium] CodeMirror injection failed: {e}")

        # Fallback: click editor + keyboard paste
        if not injected:
            try:
                from selenium.webdriver.common.keys import Keys
                editor_area = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.view-lines, .CodeMirror, [data-mode-id]')
                ))
                editor_area.click()
                time.sleep(0.5)
                editor_area.send_keys(Keys.CONTROL + 'a')
                time.sleep(0.3)
                editor_area.send_keys(Keys.DELETE)
                time.sleep(0.3)
                # Use pyperclip-style clipboard injection via JS
                driver.execute_script(
                    "navigator.clipboard.writeText(arguments[0])", code
                )
                editor_area.send_keys(Keys.CONTROL + 'v')
                time.sleep(1)
                print("[Selenium] Code pasted via keyboard.")
                injected = True
            except Exception as e:
                print(f"[Selenium] Keyboard paste failed: {e}")

        if not injected:
            return 'Error: Could not inject code into editor.'

        # ── Step 5: Click Submit ──────────────────────────────────────────
        print("[Selenium] Clicking Submit button...")
        submit_btn = None
        for selector in [
            'button[data-e2e-locator="console-submit-button"]',
            'button[data-cy="submit-code-btn"]',
            '//button[contains(text(),"Submit")]',
        ]:
            try:
                if selector.startswith('//'):
                    submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                break
            except TimeoutException:
                continue

        if not submit_btn:
            return 'Error: Submit button not found.'

        submit_btn.click()

        # ── Step 6: Wait for result (up to 45 seconds) ───────────────────
        print("[Selenium] Waiting for submission result...")
        time.sleep(8)

        result_text = None
        for selector in [
            '[data-e2e-locator="submission-result"]',
            '.text-success',
            '.text-danger',
            '[class*="result"]',
        ]:
            try:
                el = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                result_text = el.text.strip()
                if result_text:
                    break
            except TimeoutException:
                continue

        if not result_text:
            return 'Error: Timeout waiting for submission result.'

        print(f"[Selenium] Submission result: {result_text}")
        result_lower = result_text.lower()
        if 'accepted' in result_lower:
            return 'Accepted'
        elif 'wrong answer' in result_lower:
            return 'Wrong Answer'
        elif 'time limit' in result_lower:
            return 'Time Limit Exceeded'
        elif 'runtime error' in result_lower:
            return 'Runtime Error'
        elif 'compile error' in result_lower:
            return 'Compile Error'
        else:
            return result_text

    except TimeoutException as e:
        print(f"[Selenium] Submission timeout: {e}")
        return 'Error: Timeout'
    except Exception as e:
        print(f"[Selenium] Submission error: {e}")
        return f'Error: {str(e)}'
    finally:
        driver.quit()
