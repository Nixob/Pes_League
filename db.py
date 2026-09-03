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


def get_orphaned_fixtures(league_id: str):
    """Fixtures in this league where one side's player has since been
    deleted (player_id is null on that side, name kept as a snapshot).
    These are always PLAYED matches — remove_player already clears out
    any unplayed ones — left behind on purpose as real history. Surfaced
    here so the admin can optionally purge one entirely if it's throwing
    off match-count comparisons for whoever's left."""
    fixtures = list_fixtures(league_id)
    return [f for f in fixtures if f["home_player_id"] is None or f["away_player_id"] is None]


def delete_fixture(fixture_id: str):
    """Permanently deletes a single fixture row. No undo."""
    sb = get_client()
    return sb.table("fixtures").delete().eq("id", fixture_id).execute().data


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


def start_new_league(name: str, player_ids: list[str], deadline=None, leg2_deadline=None):
    """Creates a league, registers participants, and generates a full
    home & away round-robin fixture list. Player club/IGN are snapshotted
    onto each fixture at creation time. `deadline` (Leg 1) and
    `leg2_deadline` are optional datetime.date values — leave as None to
    not enforce one. They're independent since Leg 2 unlocks later."""
    if get_active_league():
        raise ValueError("There's already an active league. Complete it first.")
    if len(player_ids) < 2:
        raise ValueError("Need at least 2 players to start a league.")

    sb = get_client()
    players = {p["id"]: p for p in list_players()}

    league_row = {"name": name.strip(), "status": "active"}
    if deadline:
        league_row["deadline"] = deadline.isoformat()
    if leg2_deadline:
        league_row["leg2_deadline"] = leg2_deadline.isoformat()

    league = sb.table("leagues").insert(league_row).execute().data[0]
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


def set_league_deadline(league_id: str, deadline):
    """Sets/clears the Leg 1 deadline. deadline: a datetime.date, or None to clear."""
    sb = get_client()
    sb.table("leagues").update(
        {"deadline": deadline.isoformat() if deadline else None}
    ).eq("id", league_id).execute()


def set_league_leg2_deadline(league_id: str, deadline):
    """Sets/clears the Leg 2 deadline. deadline: a datetime.date, or None to clear."""
    sb = get_client()
    sb.table("leagues").update(
        {"leg2_deadline": deadline.isoformat() if deadline else None}
    ).eq("id", league_id).execute()


def apply_forfeit(fixture_id: str, outcome: str):
    """Records a forfeit result. outcome is 'home' or 'away' for a 1-0
    win to that side, or 'draw' for a 1-1 no-fault result (useful when
    it's genuinely unclear who's more at fault for the missed match).
    Tagged with forfeit=True so it displays distinctly from a normally-
    played match."""
    if outcome not in ("home", "away", "draw"):
        raise ValueError("outcome must be 'home', 'away', or 'draw'")
    scores = {"home": (1, 0), "away": (0, 1), "draw": (0, 0)}
    home_score, away_score = scores[outcome]
    sb = get_client()
    sb.table("fixtures").update({
        "played": True,
        "home_score": home_score,
        "away_score": away_score,
        "forfeit": True,
        "played_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", fixture_id).execute()


def auto_resolve_leg(league_id: str, leg: int) -> int:
    """Scans every still-unplayed fixture in the given leg and resolves
    it automatically: whichever side has played MORE matches in this
    leg so far gets credited a 1-0 forfeit win (the other side is the
    more likely no-show). Equal counts become a 0-0 forfeit draw, since
    there's no fair way to pick a winner. Safe to call repeatedly —
    once nothing's unplayed for that leg, it's a no-op. Returns how
    many fixtures got resolved."""
    fixtures = list_fixtures(league_id)
    leg_fixtures = [f for f in fixtures if f["leg"] == leg]

    played_count: dict[str, int] = {}
    for f in leg_fixtures:
        if f["played"]:
            played_count[f["home_player_id"]] = played_count.get(f["home_player_id"], 0) + 1
            played_count[f["away_player_id"]] = played_count.get(f["away_player_id"], 0) + 1

    unplayed = [f for f in leg_fixtures if not f["played"]]
    for f in unplayed:
        hc = played_count.get(f["home_player_id"], 0)
        ac = played_count.get(f["away_player_id"], 0)
        if hc == ac:
            apply_forfeit(f["id"], "draw")
        elif hc > ac:
            apply_forfeit(f["id"], "home")   # home played more matches -> home wins
        else:
            apply_forfeit(f["id"], "away")   # away played more matches -> away wins
    return len(unplayed)


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


# Playoff rounds reuse the existing integer `leg` column, so this feature does
# not require a new Supabase table or migration:
#   1 = league Leg 1, 2 = league Leg 2
#   3 = quarter-final Leg 1, 4 = quarter-final Leg 2
#   5 = semi-final Leg 1, 6 = semi-final Leg 2
#   7 = final (single match)
QF_LEG1, QF_LEG2 = 3, 4
SF_LEG1, SF_LEG2 = 5, 6
FINAL_LEG = 7


def league_stage_complete(league_id: str) -> bool:
    fixtures = [f for f in list_fixtures(league_id) if f["leg"] in (1, 2)]
    return bool(fixtures) and all(f["played"] for f in fixtures)


def playoffs_started(league_id: str) -> bool:
    return any(f["leg"] >= QF_LEG1 for f in list_fixtures(league_id))


def _player_snapshot(player_id: str, players: dict):
    p = players.get(player_id)
    if not p:
        raise ValueError("A playoff participant is no longer available.")
    return p


def _playoff_row(league_id, home_id, away_id, players, leg):
    home = _player_snapshot(home_id, players)
    away = _player_snapshot(away_id, players)
    return {
        "league_id": league_id,
        "home_player_id": home_id,
        "away_player_id": away_id,
        "leg": leg,
        "home_club_name": home["club_name"],
        "home_ign": home["ign"],
        "away_club_name": away["club_name"],
        "away_ign": away["ign"],
    }


def _tie_groups(fixtures, leg1, leg2):
    groups = {}
    for f in fixtures:
        if f["leg"] not in (leg1, leg2):
            continue
        key = tuple(sorted((f["home_player_id"], f["away_player_id"])))
        groups.setdefault(key, []).append(f)
    return list(groups.values())


def _tie_winner(tie, leg1, leg2, seed_order):
    """Resolve a two-legged tie using aggregate score, then old-UCL away goals.
    If both are level, the higher league seed advances as a deterministic
    fallback because the current fixture schema has no ET/penalty fields."""
    if len(tie) != 2 or not all(f["played"] for f in tie):
        return None

    aggregate = {}
    away_goals = {}
    for f in tie:
        h, a = f["home_player_id"], f["away_player_id"]
        hs, aws = f["home_score"], f["away_score"]
        aggregate[h] = aggregate.get(h, 0) + hs
        aggregate[a] = aggregate.get(a, 0) + aws
        away_goals[h] = away_goals.get(h, 0)
        away_goals[a] = away_goals.get(a, 0) + aws

    ids = list(aggregate)
    if aggregate[ids[0]] != aggregate[ids[1]]:
        return max(ids, key=lambda pid: aggregate[pid])
    if away_goals[ids[0]] != away_goals[ids[1]]:
        return max(ids, key=lambda pid: away_goals[pid])
    return min(ids, key=lambda pid: seed_order.get(pid, 999))


def create_playoffs(league_id: str) -> list[dict]:
    """Create the top-8 quarter-final bracket: 1v8, 4v5, 2v7, 3v6."""
    if playoffs_started(league_id):
        return []
    if not league_stage_complete(league_id):
        raise ValueError("All league fixtures must be completed before playoffs can start.")

    table = get_standings(league_id)
    if len(table) < 8:
        raise ValueError("Playoffs need at least 8 league participants.")
    top8 = table[:8]
    if any(r["player_id"] is None for r in top8):
        raise ValueError("All top-8 playoff teams must still have an active player record.")

    players = {p["id"]: p for p in list_players()}
    pairs = [
        (top8[0]["player_id"], top8[7]["player_id"]),
        (top8[3]["player_id"], top8[4]["player_id"]),
        (top8[1]["player_id"], top8[6]["player_id"]),
        (top8[2]["player_id"], top8[5]["player_id"]),
    ]
    rows = []
    for high, low in pairs:
        rows.append(_playoff_row(league_id, high, low, players, QF_LEG1))
        rows.append(_playoff_row(league_id, low, high, players, QF_LEG2))
    get_client().table("fixtures").insert(rows).execute()
    return rows


def _seed_order(league_id: str):
    return {r["player_id"]: i + 1 for i, r in enumerate(get_standings(league_id)[:8])}


def _round_exists(fixtures, legs):
    return any(f["leg"] in legs for f in fixtures)


def advance_playoffs(league_id: str) -> bool:
    """Automatically creates the next knockout round when the previous round is done."""
    fixtures = list_fixtures(league_id)
    if not playoffs_started(league_id):
        return False
    players = {p["id"]: p for p in list_players()}
    seeds = _seed_order(league_id)

    # Quarter-finals -> semi-finals.
    if not _round_exists(fixtures, (SF_LEG1, SF_LEG2)):
        groups = _tie_groups(fixtures, QF_LEG1, QF_LEG2)
        if len(groups) != 4 or not all(len(g) == 2 and all(f["played"] for f in g) for g in groups):
            return False

        winners_by_seeds = {}
        for tie in groups:
            ids = {pid for f in tie for pid in (f["home_player_id"], f["away_player_id"])}
            seed_pair = tuple(sorted(seeds.get(pid, 99) for pid in ids))
            winners_by_seeds[seed_pair] = _tie_winner(tie, QF_LEG1, QF_LEG2, seeds)

        sf_pairs = [
            (winners_by_seeds.get((1, 8)), winners_by_seeds.get((4, 5))),
            (winners_by_seeds.get((2, 7)), winners_by_seeds.get((3, 6))),
        ]
        if not all(a and b for a, b in sf_pairs):
            return False

        rows = []
        for a, b in sf_pairs:
            rows.append(_playoff_row(league_id, a, b, players, SF_LEG1))
            rows.append(_playoff_row(league_id, b, a, players, SF_LEG2))
        get_client().table("fixtures").insert(rows).execute()
        return True

    # Semi-finals -> final.
    if not _round_exists(fixtures, (FINAL_LEG,)):
        groups = _tie_groups(fixtures, SF_LEG1, SF_LEG2)
        if len(groups) != 2 or not all(len(g) == 2 and all(f["played"] for f in g) for g in groups):
            return False
        winners = [_tie_winner(g, SF_LEG1, SF_LEG2, seeds) for g in groups]
        if not all(winners):
            return False
        get_client().table("fixtures").insert([
            _playoff_row(league_id, winners[0], winners[1], players, FINAL_LEG)
        ]).execute()
        return True

    return False


def playoff_champion(league_id: str):
    final = [f for f in list_fixtures(league_id) if f["leg"] == FINAL_LEG]
    if len(final) != 1 or not final[0]["played"]:
        return None
    f = final[0]
    if f["home_score"] > f["away_score"]:
        return f["home_player_id"]
    if f["away_score"] > f["home_score"]:
        return f["away_player_id"]
    return None


def complete_league(league_id: str):
    """Archive the season after the playoff final has produced a champion."""
    champion_id = playoff_champion(league_id)
    if not champion_id:
        raise ValueError("The playoff final must be completed before the league can be archived.")
    get_client().table("leagues").update({
        "status": "completed",
        "winner_player_id": champion_id,
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


def get_fixture(fixture_id: str):
    sb = get_client()
    res = sb.table("fixtures").select("*").eq("id", fixture_id).limit(1).execute().data
    return res[0] if res else None


def leg1_complete(league_id: str) -> bool:
    """True once every Leg 1 fixture in the league has been played."""
    fixtures = list_fixtures(league_id)
    leg1 = [f for f in fixtures if f["leg"] == 1]
    return bool(leg1) and all(f["played"] for f in leg1)


def unlock_leg2(league_id: str):
    sb = get_client()
    return sb.table("leagues").update({"leg2_unlocked": True}).eq("id", league_id).execute()


def next_fixture_for_player(league_id: str, player_id: str):
    fixtures = list_fixtures(league_id)
    for f in fixtures:
        if not f["played"] and player_id in (f["home_player_id"], f["away_player_id"]):
            return f
    return None


def submit_result(fixture_id: str, home_score: int, away_score: int):
    """Save a result. The playoff final must have a winner."""
    fixture = get_fixture(fixture_id)
    if fixture and fixture["leg"] == FINAL_LEG and home_score == away_score:
        raise ValueError("The playoff final must have a winner (include the shootout winner in the recorded result).")
    sb = get_client()
    sb.table("fixtures").update({
        "played": True,
        "home_score": home_score,
        "away_score": away_score,
        "forfeit": False,
        "played_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", fixture_id).execute()


def unmark_result(fixture_id: str):
    """Untick — in case someone fat-fingers a score, or a forfeit needs
    reversing (e.g. the player showed up after all)."""
    sb = get_client()
    sb.table("fixtures").update({
        "played": False,
        "home_score": None,
        "away_score": None,
        "forfeit": False,
        "played_at": None,
    }).eq("id", fixture_id).execute()


# --------------------------------------------------------------- standings --

def get_standings(league_id: str):
    """Builds the league table from fixtures' own snapshot names — works
    even if a player has since been deleted. Groups by player_id when the
    live link still exists, otherwise falls back to the snapshotted
    club+IGN so a deleted player's two legs still combine into one row."""
    # Playoff rows share the fixtures table but must never affect league standings.
    fixtures = [f for f in list_fixtures(league_id) if f["leg"] in (1, 2)]
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
