# eFootball Mobile — GC League

A Streamlit + Supabase site to run a mini home/away round-robin league
for the group chat.

## What it does
- Anyone can submit their club name + IGN to join — sits as **pending** until you (admin) approve them
- Admin starts a league from the approved player pool → auto-generates a full home & away round-robin fixture list
- Anyone can tick a fixture as played and enter the scoreline (honor system, no login needed for that part)
- Table auto-computes from ticked results (3 pts win / 1 draw / 0 loss)
- When a cycle's done, admin hits "Complete league" — table gets locked, winner tagged, and it moves into History so a new league can start
- Player cap: 25 approved players at a time

## 1. Set up Supabase
1. Create a free project at [supabase.com](https://supabase.com)
2. Go to the SQL Editor → paste in the contents of `schema.sql` → Run
3. Go to Project Settings → API → copy your **Project URL** and **anon public key**

## 2. Configure secrets
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in:
```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "your-anon-public-key"
ADMIN_PASSWORD = "pick-something"
```
If you deploy on **Streamlit Community Cloud**, don't commit this file — paste
the same three keys into your app's Settings → Secrets instead.

## 3. Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 4. Deploy (free)
Push this folder to a GitHub repo, then on
[share.streamlit.io](https://share.streamlit.io):
1. New app → point it at your repo → main file `app.py`
2. Paste your secrets in the app's Secrets settings
3. Deploy — share the URL with the boys

## Notes / things to keep an eye on
- Free Supabase projects pause after a week of no activity — a login to the
  dashboard wakes it back up. Fine for a GC league that gets used regularly.
- The admin password is a single shared password (set in secrets), not
  per-user login — simplest option for a small trusted group.
- Only one league can be active at a time by design — finish one before
  starting the next.
