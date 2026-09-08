"""
HOW TO USE THIS FILE:
1. Put this file in the same folder as db.py (and your .streamlit/secrets.toml
   with SUPABASE_URL / SUPABASE_KEY — same setup the app itself uses).
2. Run it:  python fix_corrupted_sf.py
3. It will list every playoff fixture (quarter-final, semi-final, final) for
   the current active league, clearly labeled.
4. It will only ever delete rows you explicitly type the ID for, and only
   after you type "yes" to confirm — it will never delete anything on its own.
5. It refuses to delete any fixture that's already been played, as a safety
   guard, since undoing a played result should go through the app's own
   Undo button, not this script.
"""

import db

ROUND_NAMES = {
    db.QF_LEG1: "QF (Leg 1)", db.QF_LEG2: "QF (Leg 2)",
    db.SF_LEG1: "SF (Leg 1)", db.SF_LEG2: "SF (Leg 2)",
    db.FINAL_LEG: "Final",
}

league = db.get_active_league()
if not league:
    print("No active league found.")
    raise SystemExit

fixtures = [f for f in db.list_fixtures(league["id"]) if f["leg"] >= db.QF_LEG1]
if not fixtures:
    print("No playoff fixtures exist yet for the active league.")
    raise SystemExit

print(f"\nPlayoff fixtures for: {league['name']}\n")
print(f"{'ID':<38} {'Round':<12} {'Home':<15} {'Away':<15} {'Played':<8} {'Score'}")
print("-" * 100)
for f in fixtures:
    score = f"{f['home_score']}-{f['away_score']}" if f["played"] else "-"
    print(f"{f['id']:<38} {ROUND_NAMES.get(f['leg'], f['leg']):<12} "
          f"{f['home_ign']:<15} {f['away_ign']:<15} {str(f['played']):<8} {score}")

print("\nPaste the ID(s) of the fixture(s) you want to delete, separated by commas.")
print("(Leave blank and press Enter to exit without deleting anything.)")
raw = input("Fixture ID(s) to delete: ").strip()

if not raw:
    print("Nothing entered — exiting without changes.")
    raise SystemExit

target_ids = [x.strip() for x in raw.split(",") if x.strip()]
targets = [f for f in fixtures if f["id"] in target_ids]

missing = set(target_ids) - {f["id"] for f in targets}
if missing:
    print(f"\nCould not find these IDs among the playoff fixtures above, aborting: {missing}")
    raise SystemExit

already_played = [f for f in targets if f["played"]]
if already_played:
    print("\nRefusing to continue — the following fixture(s) have already been played.")
    print("Use the app's own Undo button for played results, not this script:")
    for f in already_played:
        print(f"  {f['id']}  {f['home_ign']} vs {f['away_ign']}  ({f['home_score']}-{f['away_score']})")
    raise SystemExit

print("\nAbout to permanently delete:")
for f in targets:
    print(f"  {f['id']}  {ROUND_NAMES.get(f['leg'], f['leg'])}  {f['home_ign']} vs {f['away_ign']}")

confirm = input("\nType 'yes' to confirm deletion: ").strip().lower()
if confirm != "yes":
    print("Not confirmed — exiting without changes.")
    raise SystemExit

sb = db.get_client()
for f in targets:
    sb.table("fixtures").delete().eq("id", f["id"]).execute()
    print(f"Deleted {f['id']}")

print("\nDone. Reload the Playoffs page in the app to see the change.")
