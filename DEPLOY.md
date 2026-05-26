# Complete deployment guide (Render + GitHub)

Follow these steps in order. Total time: ~30–45 minutes.

---

## Part A — Push code to GitHub

### A1. Create a GitHub account (if needed)

Go to https://github.com and sign up.

### A2. Create a new repository

1. Click **+** → **New repository**
2. Name: `breathe-esg` (or any name)
3. **Private** is fine (assignment allows private)
4. Do **not** add README, .gitignore, or license (you already have them)
5. Click **Create repository**

### A3. Push your project (PowerShell)

Replace `YOUR_GITHUB_USERNAME` with your real username:

```powershell
cd d:\Desktop2\project

git add -A
git commit -m "Breathe ESG prototype: ingestion and review dashboard"

git branch -M main
git remote add origin https://github.com/gowrisankararao/breathe-esg.git
git push -u origin main
```

If Git asks you to log in, use a **Personal Access Token** (not password):
- GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic) → scope: `repo`

---

## Part B — Deploy on Render (FREE — no payment)

### Why Render asked for payment

The old `render.yaml` included a **PostgreSQL database**. Render **no longer offers free Postgres**, so it asks you to add a card.

**Fix:** The repo now uses **SQLite** on a **free web service only** (no database addon). Pull the latest code from GitHub before deploying.

### B1. Create Render account

1. Go to https://render.com
2. Sign up with **GitHub**

### B2. Deploy (choose ONE method)

#### Method 1 — Blueprint (recommended)

1. Dashboard → **New +** → **Blueprint**
2. Select repo **`gowrisankararao/breathe-esg`**
3. You should see **only one** service: `breathe-esg` (no database, no payment)
4. Click **Apply** → wait 10–15 minutes

#### Method 2 — Manual (if Blueprint still asks for payment)

1. **New +** → **Web Service**
2. Connect **`breathe-esg`** repo
3. Settings:
   - **Build command:** `./build.sh`
   - **Start command:** `cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan:** Free
4. **Do not** add a PostgreSQL database
5. Create Web Service

> **Note:** Free SQLite on Render resets if the service is redeployed. `seed_demo` runs on each deploy so login `analyst` / `demo1234` always works.

### B3. Get your live URL

1. Open the **breathe-esg** web service (not the database)
2. Top of page shows URL like: `https://breathe-esg-xxxx.onrender.com`
3. Copy that URL — this goes in your submission email

### B4. Set environment variables (required)

In the web service → **Environment**:

| Key | Value |
|-----|--------|
| `CORS_ALLOWED_ORIGINS` | `https://breathe-esg-xxxx.onrender.com` (your exact URL, no trailing slash) |
| `CSRF_TRUSTED_ORIGINS` | `https://breathe-esg-xxxx.onrender.com` (same URL) |

Click **Save Changes**. Render will redeploy automatically (~2–5 min).

### B5. Test the live app

1. Open your Render URL in the browser
2. **First load may take 30–60 seconds** (free tier wakes from sleep)
3. Login: **analyst** / **demo1234**
4. You should see the dashboard (~20 records)
5. Test **Review queue** and **Ingest data**

If you see a blank page or login fails, check **Logs** in Render for errors.

---

## Part C — Share repo with Breathe ESG

On GitHub → your repo → **Settings** → **Collaborators** (or **Manage access**):

Invite these emails (read access is enough):

- saurav@breatheesg.com
- rahul@breatheesg.com
- shivang@breatheesg.com

---

## Part D — Submission email

Reply to the assignment email with something like:

```
Subject: Breathe ESG Tech Intern Assignment — [Your Name]

Hi,

Please find my submission below:

GitHub repository: https://github.com/YOUR_USERNAME/breathe-esg
Live application: https://breathe-esg-xxxx.onrender.com

Login credentials:
  Username: analyst
  Password: demo1234

Documentation in the repo:
  - MODEL.md
  - DECISIONS.md
  - TRADEOFFS.md
  - SOURCES.md

Thank you,
[Your Name]
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build failed on Render | Open **Logs** → look for npm or Python errors; ensure `package-lock.json` is committed |
| 502 / app not loading | Wait for deploy to finish; check build logs; do not add a paid database |
| Login works locally but not on Render | Set `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` to your Render URL |
| Static page, no styling | Redeploy after a successful build (frontend must build in `build.sh`) |
| Very slow first visit | Normal on Render free tier — service sleeps when idle |

---

## Checklist before you submit

- [ ] GitHub repo pushed
- [ ] Render deploy **Live** (green)
- [ ] Live URL opens login page
- [ ] Login works on production URL
- [ ] Three collaborators invited on GitHub
- [ ] Email sent with repo + URL + credentials
