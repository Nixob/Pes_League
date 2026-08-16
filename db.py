"""
All Supabase reads/writes for the eFootball GC League app live here,
so app.py just calls plain Python functions.
"""

import itertools
from datetime import datetime, timezone

import streamlit as st
from supabase import create_client, Client

MAX_PLAYERS = 25


@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# ---------------------------------------------------------------- players --

def list_players(status: str | None = None, active_only: bool = False):
    sb = get_client()
    q = sb.table("players").select("*").order("club_name")
    if status:
        q = q.eq("status", status)
    if active_only:
        q = q.eq("active", True)
    return q.execute().data


def player_count(status: str = "approved") -> int:
    return len(list_players(status=status))


def register_player(club_name: str, ign: str):
    """Self-registration from the public side: always starts 'pending'
    until the admin approves it."""
    if player_count(status="approved") >= MAX_PLAYERS:
        raise ValueError(f"Player cap reached ({MAX_PLAYERS}). Ask the admin to remove someone first.")
    sb = get_client()
    return sb.table("players").insert(
        {"club_name": club_name.strip(), "ign": ign.strip(), "status": "pending"}
    ).execute().data


def admin_add_player(club_name: str, ign: str):
    """Admin adding someone directly — skips the pending step."""
    if player_count(status="approved") >= MAX_PLAYERS:
        raise ValueError(f"Player cap reached ({MAX_PLAYERS}). Remove someone first.")
    sb = get_client()
    return sb.table("players").insert(
        {"club_name": club_name.strip(), "ign": ign.strip(), "status": "approved"}
    ).execute().data


def approve_player(player_id: str):
    if player_count(status="approved") >= MAX_PLAYERS:
        raise ValueError(f"Player cap reached ({MAX_PLAYERS}). Remove someone before approving more.")
    sb = get_client()
    return sb.table("players").update({"status": "approved"}).eq("id", player_id).execute().data


def reject_player(player_id: str):
    sb = get_client()
    return sb.table("players").update({"status": "rejected"}).eq("id", player_id).execute().data


def update_player(player_id: str, club_name: str, ign: str, active: bool):
    sb = get_client()
    return sb.table("players").update(
        {"club_name": club_name.strip(), "ign": ign.strip(), "active": active}
    ).eq("id", player_id).execute().data


def remove_player(player_id: str):
    """Hard-deletes a player. Any of their fixtures already PLAYED are left
    untouched — that's real history, and it keeps other players' records
    accurate. Any UNPLAYED fixtures involving them are deleted too, so they
    don't linger as a ghost row (0 played, 0 pts) in the standings table."""
    sb = get_client()
    sb.table("fixtures").delete().eq("played", False).or_(
        f"home_player_id.eq.{player_id},away_player_id.eq.{player_id}"
    ).execute()
    return sb.table("players").delete().eq("id", player_id).execute().data


# ----------------------------------------------------------------- leagues --

def get_active_league():
    sb = get_client()
    res = sb.table("leagues").select("*").eq("status", "active").limit(1).execute().data
    return res[0] if res else None


def list_completed_leagues():
    sb = get_client()
    return sb.table("leagues").select(
        "*, winner:winner_player_id(club_name, ign)"
    ).eq("status", "completed").order("completed_at", desc=True).execute().data


def start_new_league(name: str, player_ids: list[str]):
    """Creates a league, registers participants, and generates a full
    home & away round-robin fixture list. Player club/IGN are snapshotted
    onto each fixture at creation time."""
    if get_active_league():
        raise ValueError("There's already an active league. Complete it first.")
    if len(player_ids) < 2:
        raise ValueError("Need at least 2 players to start a league.")

    sb = get_client()
    players = {p["id"]: p for p in list_players()}

    league = sb.table("leagues").insert({"name": name.strip(), "status": "active"}) \
        .execute().data[0]
    league_id = league["id"]

    sb.table("league_participants").insert(
        [{"league_id": league_id, "player_id": pid} for pid in player_ids]
    ).execute()

    fixtures_rows = []
    for a, b in itertools.combinations(player_ids, 2):
        pa, pb = players[a], players[b]
        fixtures_rows.append({
            "league_id": league_id, "home_player_id": a, "away_player_id": b, "leg": 1,
            "home_club_name": pa["club_name"], "home_ign": pa["ign"],
            "away_club_name": pb["club_name"], "away_ign": pb["ign"],
        })
        fixtures_rows.append({
            "league_id": league_id, "home_player_id": b, "away_player_id": a, "leg": 2,
            "home_club_name": pb["club_name"], "home_ign": pb["ign"],
            "away_club_name": pa["club_name"], "away_ign": pa["ign"],
        })
    sb.table("fixtures").insert(fixtures_rows).execute()
    return league


def get_league_participant_ids(league_id: str) -> list[str]:
    sb = get_client()
    rows = sb.table("league_participants").select("player_id").eq("league_id", league_id).execute().data
    return [r["player_id"] for r in rows]


def add_player_to_league(league_id: str, player_id: str):
    """Adds a player to an already-running league. Generates home & away
    fixtures against everyone currently in the league — existing results
    are untouched. Doesn't retroactively rebalance the table, it just
    slots the new player in with fresh fixtures from here on."""
    existing_ids = get_league_participant_ids(league_id)
    if player_id in existing_ids:
        raise ValueError("That player is already in this league.")

    sb = get_client()
    players = {p["id"]: p for p in list_players()}
    new_p = players[player_id]

    sb.table("league_participants").insert(
        {"league_id": league_id, "player_id": player_id}
    ).execute()

    fixtures_rows = []
    for other_id in existing_ids:
        other = players[other_id]
        fixtures_rows.append({
            "league_id": league_id, "home_player_id": player_id, "away_player_id": other_id, "leg": 1,
            "home_club_name": new_p["club_name"], "home_ign": new_p["ign"],
            "away_club_name": other["club_name"], "away_ign": other["ign"],
        })
        fixtures_rows.append({
            "league_id": league_id, "home_player_id": other_id, "away_player_id": player_id, "leg": 2,
            "home_club_name": other["club_name"], "home_ign": other["ign"],
            "away_club_name": new_p["club_name"], "away_ign": new_p["ign"],
        })
    if fixtures_rows:
        sb.table("fixtures").insert(fixtures_rows).execute()
    return new_p


def complete_league(league_id: str):
    """Locks the table, tags the winner, archives the league."""
    table = get_standings(league_id)
    if not table:
        raise ValueError("No results recorded — nothing to complete.")
    winner_id = table[0]["player_id"]  # may be None if that player was since deleted
    sb = get_client()
    sb.table("leagues").update({
        "status": "completed",
        "winner_player_id": winner_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", league_id).execute()


def delete_league(league_id: str):
    """Deletes a league and (via cascade) its fixtures and participants.
    This permanently removes that season's history — no undo."""
    sb = get_client()
    return sb.table("leagues").delete().eq("id", league_id).execute().data


# ---------------------------------------------------------------- fixtures --

def list_fixtures(league_id: str):
    sb = get_client()
    return sb.table("fixtures").select("*") \
        .eq("league_id", league_id).order("leg").execute().data


def next_fixture_for_player(league_id: str, player_id: str):
    fixtures = list_fixtures(league_id)
    for f in fixtures:
        if not f["played"] and player_id in (f["home_player_id"], f["away_player_id"]):
            return f
    return None


def submit_result(fixture_id: str, home_score: int, away_score: int):
    """Ticking a fixture as played — this is the 'tick mark' action."""
    sb = get_client()
    sb.table("fixtures").update({
        "played": True,
        "home_score": home_score,
        "away_score": away_score,
        "played_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", fixture_id).execute()


def unmark_result(fixture_id: str):
    """Untick — in case someone fat-fingers a score."""
    sb = get_client()
    sb.table("fixtures").update({
        "played": False,
        "home_score": None,
        "away_score": None,
        "played_at": None,
    }).eq("id", fixture_id).execute()


# --------------------------------------------------------------- standings --

def get_standings(league_id: str):
    """Builds the league table from fixtures' own snapshot names — works
    even if a player has since been deleted. Groups by player_id when the
    live link still exists, otherwise falls back to the snapshotted
    club+IGN so a deleted player's two legs still combine into one row."""
    fixtures = list_fixtures(league_id)
    stats = {}

    def side_key(f, side):
        pid = f[f"{side}_player_id"]
        if pid:
            return pid
        return f"deleted:{f[f'{side}_club_name']}|{f[f'{side}_ign']}"

    def ensure(f, side):
        key = side_key(f, side)
        if key not in stats:
            stats[key] = {
                "player_id": f[f"{side}_player_id"],
                "club_name": f[f"{side}_club_name"],
                "ign": f[f"{side}_ign"],
                "played": 0, "won": 0, "drawn": 0, "lost": 0,
                "gf": 0, "ga": 0, "gd": 0, "points": 0,
            }
        return stats[key]

    for f in fixtures:
        h, a = ensure(f, "home"), ensure(f, "away")
        if not f["played"]:
            continue
        hs, aws = f["home_score"], f["away_score"]
        h["played"] += 1
        a["played"] += 1
        h["gf"] += hs
        h["ga"] += aws
        a["gf"] += aws
        a["ga"] += hs
        if hs > aws:
            h["won"] += 1
            h["points"] += 3
            a["lost"] += 1
        elif hs < aws:
            a["won"] += 1
            a["points"] += 3
            h["lost"] += 1
        else:
            h["drawn"] += 1
            a["drawn"] += 1
            h["points"] += 1
            a["points"] += 1

    for s in stats.values():
        s["gd"] = s["gf"] - s["ga"]

    return sorted(stats.values(), key=lambda s: (-s["points"], -s["gd"], -s["gf"]))
