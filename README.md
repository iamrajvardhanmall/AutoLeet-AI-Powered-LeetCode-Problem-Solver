# 🤖 LeetCode Auto-Solver

An AI-powered full-stack web application that **automatically scrapes, solves, and submits LeetCode problems** on your behalf — using Groq's free Llama 3.3 70B model and Selenium browser automation.

---

## ✨ Features

- 🔐 **Manual login via real Chrome** — bypasses bot detection using `undetected_chromedriver`
- 🔍 **Problem scraping** via LeetCode's GraphQL API (no browser needed for reading)
- 🧠 **AI solution generation** using Groq's free Llama 3.3 70B model
- 🚀 **Automated submission** — injects solution into LeetCode via browser `fetch()` calls
- 📊 **Result polling** — waits for and captures the final verdict (Accepted, Wrong Answer, TLE, etc.)
- 💾 **Result caching** — skips re-solving if an accepted solution already exists in the database
- 📜 **History dashboard** — view all previously solved problems and solution attempts

---

## 🖥️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, React Router v6, Axios |
| Backend | Django 4.2, Django REST Framework |
| AI | [Groq API](https://console.groq.com) — Llama 3.3 70B (free) |
| Browser Automation | Selenium + `undetected_chromedriver` |
| Database | SQLite |

---

## 📁 Project Structure

```
Leetcode/
├── backend/                        # Django backend
│   ├── manage.py
│   ├── requirements.txt
│   ├── leetcode_cookies.json       # Saved session cookies (auto-generated)
│   ├── leetcode_project/           # Django project settings & root URLs
│   ├── solver/                     # Core app: login, scrape, solve, submit
│   │   ├── models.py               # Problem + Solution DB models
│   │   ├── views.py                # 8-step solve pipeline
│   │   ├── selenium_utils.py       # Login, scraping, browser submission
│   │   ├── gpt_utils.py            # Groq AI integration
│   │   ├── serializers.py          # DRF serializers
│   │   └── urls.py
│   └── dashboard/                  # Read-only history endpoints
│       ├── views.py
│       └── urls.py
└── frontend/                       # React frontend
    ├── package.json
    └── src/
        ├── api.js                  # Axios client
        ├── App.js                  # Router setup
        ├── pages/
        │   ├── HomePage.js         # Login flow + solve form
        │   ├── HistoryPage.js      # Table of solved problems
        │   └── ResultPage.js       # Detail view per problem
        └── components/
            ├── Navbar.js
            └── Spinner.js
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Chrome installed
- A free [Groq API key](https://console.groq.com/keys)

---

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Leetcode
```

---

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo GROQ_API_KEY=your_groq_api_key_here > .env

# Run migrations
python manage.py migrate

# Start the Django server
python manage.py runserver
```

> The backend runs at `http://127.0.0.1:8000`

---

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the React app
npm start
```

> The frontend runs at `http://localhost:3000`

---

## 🚀 Usage

1. **Open** `http://localhost:3000` in your browser
2. **Login** — Click **"Open Login Browser"** → a Chrome window opens → log in to LeetCode manually → the window closes automatically once login is detected
3. **Solve** — Enter a LeetCode problem number (e.g., `1`) and click **"Solve"**
4. **Wait** — The backend scrapes the problem, generates a Python solution with AI, and submits it (~30–90 seconds)
5. **View result** — The submission verdict appears inline on the home page
6. **History** — Click **"History"** in the navbar to see all previous attempts

---

## 🔄 How It Works — Full Pipeline

```
User enters problem number
        ↓
Check if accepted solution already cached in DB → return immediately if yes
        ↓
Scrape problem title + description via LeetCode GraphQL API
        ↓
Save Problem to SQLite
        ↓
Send description to Groq (Llama 3.3 70B) → receive Python solution
        ↓
Open Chrome with saved session cookies
        ↓
Navigate to problem page → POST solution via browser fetch() (bypasses Cloudflare)
        ↓
Poll /submissions/detail/<id>/check/ until state = SUCCESS
        ↓
Save Solution + status to SQLite → return result to frontend
```

---

## 🌐 API Reference

### Solver Endpoints

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/solver/login-status/` | Check if LeetCode cookies are saved |
| `POST` | `/api/solver/start-login/` | Open Chrome for manual login (blocks up to 3 min) |
| `POST` | `/api/solver/logout/` | Delete saved cookies |
| `POST` | `/api/solver/solve/` | Run the full scrape → AI → submit pipeline |

**`POST /api/solver/solve/` — Request Body:**
```json
{ "problem_number": 1 }
```

**Response:**
```json
{
  "problem_number": 1,
  "title": "Two Sum",
  "description": "...",
  "generated_code": "class Solution:\n    ...",
  "submission_status": "accepted",
  "cached": false
}
```

### Dashboard Endpoints

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/dashboard/history/` | List all problems (newest first) |
| `GET` | `/api/dashboard/history/<id>/` | Problem detail with all solution attempts |

---

## 🗄️ Database Models

### `Problem`
| Field | Type | Description |
|---|---|---|
| `problem_number` | Integer (unique) | LeetCode problem number |
| `title` | String | Problem title |
| `description` | Text | Full problem description |
| `created_at` | DateTime | When first scraped |

### `Solution`
| Field | Type | Description |
|---|---|---|
| `problem` | FK → Problem | Associated problem |
| `generated_code` | Text | Python code generated by AI |
| `submission_status` | String | `accepted` / `wrong_answer` / `tle` / `error` / `pending` |
| `created_at` | DateTime | When submitted |

---

## 🛡️ Anti-Bot Detection Strategy

LeetCode uses Cloudflare to block automated requests. This project works around it in two ways:

1. **Login** — Uses `undetected_chromedriver` (patches Chrome binary signatures) so Cloudflare does not flag the browser
2. **Submission** — Instead of sending raw HTTP requests, the code navigates to the problem page in the real browser and fires the submission via `driver.execute_async_script()` with a `fetch()` call — indistinguishable from a real user action

---

## 📝 Notes

- **Groq API** is completely free (no credit card required). Get your key at [console.groq.com/keys](https://console.groq.com/keys)
- The Axios client has a **5-minute timeout** to accommodate Selenium startup + AI inference time
- The AI solution is always wrapped in `class Solution:` — enforced both via prompt engineering and a post-processing fallback
- Cookies are persisted to `backend/leetcode_cookies.json` and reused across requests; re-login is only required when they expire
- A legacy pure-Selenium submission method (`_submit_solution_selenium`) exists in `selenium_utils.py` as reference but is no longer used

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `GROQ_API_KEY not set` | Create `backend/.env` with `GROQ_API_KEY=...` |
| Chrome window doesn't open | Ensure Google Chrome is installed and up to date |
| `SessionNotCreatedException` | Update `undetected-chromedriver`: `pip install -U undetected-chromedriver` |
| `Not logged in` error | Click "Open Login Browser" and complete login; cookies may have expired |
| Frontend can't reach backend | Ensure Django server is running on port `8000` |
| Submission returns `Wrong Answer` | Re-run solve — Groq may generate a different solution each time |

---

## 📄 License

MIT License — free to use, modify, and distribute.
