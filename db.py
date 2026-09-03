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
    """Ticking a fixture as played — this is the 'tick mark' action.
    Always clears any forfeit flag, since this is a real submitted result."""
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



# ----------------------------------------------------------------- playoffs --

def generate_playoffs(league_id: str):
    """Generate QF fixtures for the top 8 players from the league standings.
    Deletes any existing playoff fixtures for this league first.
    Raises ValueError if fewer than 8 players."""
    sb = get_client()
    # Delete existing playoff fixtures for this league
    sb.table("playoff_fixtures").delete().eq("league_id", league_id).execute()

    standings = get_standings(league_id)
    if len(standings) < 8:
        raise ValueError("Need at least 8 players to generate playoffs.")

    # Top 8 sorted by points, GD, GF (already sorted from get_standings)
    top8 = standings[:8]
    # Seed: 1 vs 8, 2 vs 7, 3 vs 6, 4 vs 5
    pairings = [(0, 7), (1, 6), (2, 5), (3, 4)]
    fixtures = []
    for idx, (a, b) in enumerate(pairings, start=1):
        home = top8[a]
        away = top8[b]
        # Leg 1
        fixtures.append({
            "league_id": league_id,
            "round": 1,
            "match_index": idx,
            "home_player_id": home["player_id"],
            "away_player_id": away["player_id"],
            "home_club_name": home["club_name"],
            "home_ign": home["ign"],
            "away_club_name": away["club_name"],
            "away_ign": away["ign"],
            "leg": 1,
        })
        # Leg 2 (swap home/away)
        fixtures.append({
            "league_id": league_id,
            "round": 1,
            "match_index": idx,
            "home_player_id": away["player_id"],
            "away_player_id": home["player_id"],
            "home_club_name": away["club_name"],
            "home_ign": away["ign"],
            "away_club_name": home["club_name"],
            "away_ign": home["ign"],
            "leg": 2,
        })
    sb.table("playoff_fixtures").insert(fixtures).execute()
    return fixtures


def get_playoff_fixtures(league_id: str):
    sb = get_client()
    return sb.table("playoff_fixtures").select("*") \
        .eq("league_id", league_id) \
        .order("round", "match_index", "leg") \
        .execute().data


def update_playoff_score(fixture_id: str, home_score: int, away_score: int):
    sb = get_client()
    sb.table("playoff_fixtures").update({
        "played": True,
        "home_score": home_score,
        "away_score": away_score,
        "played_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", fixture_id).execute()


def unmark_playoff_score(fixture_id: str):
    sb = get_client()
    sb.table("playoff_fixtures").update({
        "played": False,
        "home_score": None,
        "away_score": None,
        "played_at": None,
    }).eq("id", fixture_id).execute()


def get_playoff_ties(league_id: int, round_num: int):
    """Return ties (grouped by match_index) for a given round,
    with aggregate scores and away goals computed."""
    fixtures = get_playoff_fixtures(league_id)
    ties = {}
    for f in fixtures:
        if f["round"] != round_num:
            continue
        mi = f["match_index"]
        if mi not in ties:
            ties[mi] = {"home": None, "away": None, "leg1": None, "leg2": None}
        if f["leg"] == 1:
            ties[mi]["leg1"] = f
            # home team in tie is home of leg1
            ties[mi]["home"] = {
                "player_id": f["home_player_id"],
                "club_name": f["home_club_name"],
                "ign": f["home_ign"],
            }
            ties[mi]["away"] = {
                "player_id": f["away_player_id"],
                "club_name": f["away_club_name"],
                "ign": f["away_ign"],
            }
        else:  # leg 2
            ties[mi]["leg2"] = f
    return ties


def compute_aggregate(leg1, leg2):
    """Return (home_agg, away_agg, home_away_goals, away_away_goals, winner_id)"""
    if not leg1 or not leg2:
        return None, None, None, None, None
    h1, a1 = leg1["home_score"], leg1["away_score"]
    h2, a2 = leg2["home_score"], leg2["away_score"]
    # Aggregate
    agg_home = h1 + h2  # home team in tie is leg1 home
    agg_away = a1 + a2  # away team in tie is leg1 away
    # Away goals: home team's away goals = a2 (scored in leg2 away), away team's away goals = a1 (scored in leg1 away)
    away_goals_home = a2
    away_goals_away = a1
    winner = None
    if agg_home > agg_away:
        winner = leg1["home_player_id"]
    elif agg_away > agg_home:
        winner = leg1["away_player_id"]
    else:
        # Aggregate tied -> compare away goals
        if away_goals_home > away_goals_away:
            winner = leg1["home_player_id"]
        elif away_goals_away > away_goals_home:
            winner = leg1["away_player_id"]
        else:
            # Still tied -> higher seed wins (we store seed from standings)
            # We'll handle by raising or returning None; in UI we'll ask admin
            winner = None  # unresolved
    return agg_home, agg_away, away_goals_home, away_goals_away, winner


def advance_playoff_round(league_id: str, current_round: int):
    """After all matches of current_round are played, compute winners,
    create next round fixtures (if current_round < 3).
    Returns the number of ties advanced."""
    ties = get_playoff_ties(league_id, current_round)
    all_played = True
    for mi, tie in ties.items():
        if not tie["leg1"] or not tie["leg2"] or not tie["leg1"]["played"] or not tie["leg2"]["played"]:
            all_played = False
            break
    if not all_played:
        raise ValueError("Not all matches in this round have been played.")
    winners = []
    for mi, tie in ties.items():
        agg_home, agg_away, away_home, away_away, winner_id = compute_aggregate(tie["leg1"], tie["leg2"])
        if winner_id is None:
            # Still tied -> we'll use higher seed (lower rank from standings)
            # We need to get seed: we can fetch standings at generation time? 
            # For simplicity, we'll store seed in a separate table or compute from name? 
            # Better: we can ask admin to pick winner. We'll raise error.
            raise ValueError(f"Match {mi} is still tied after away goals. Please override manually.")
        winners.append(winner_id)

    if current_round == 1:
        # QF -> SF: 4 winners, pair them: winner of QF1 vs QF4, QF2 vs QF3
        # But we need match_index mapping: QF1 (idx1) vs QF4 (idx4), QF2 vs QF3
        # We'll order winners by match_index
        winners_by_idx = {mi: winners[mi-1] for mi in range(1,5)}  # mi 1..4
        sf_pairings = [(1,4), (2,3)]
        next_round = 2
        fixtures = []
        for idx, (a, b) in enumerate(sf_pairings, start=1):
            home_id = winners_by_idx[a]
            away_id = winners_by_idx[b]
            # Get player details
            players = {p["id"]: p for p in list_players()}
            home = players.get(home_id)
            away = players.get(away_id)
            if not home or not away:
                raise ValueError("Player not found.")
            # Leg 1
            fixtures.append({
                "league_id": league_id,
                "round": next_round,
                "match_index": idx,
                "home_player_id": home_id,
                "away_player_id": away_id,
                "home_club_name": home["club_name"],
                "home_ign": home["ign"],
                "away_club_name": away["club_name"],
                "away_ign": away["ign"],
                "leg": 1,
            })
            # Leg 2
            fixtures.append({
                "league_id": league_id,
                "round": next_round,
                "match_index": idx,
                "home_player_id": away_id,
                "away_player_id": home_id,
                "home_club_name": away["club_name"],
                "home_ign": away["ign"],
                "away_club_name": home["club_name"],
                "away_ign": home["ign"],
                "leg": 2,
            })
        sb = get_client()
        sb.table("playoff_fixtures").insert(fixtures).execute()
        return len(winners)

    elif current_round == 2:
        # SF -> Final: 2 winners, single leg
        winners_by_idx = {mi: winners[mi-1] for mi in range(1,3)}
        home_id = winners_by_idx[1]
        away_id = winners_by_idx[2]
        players = {p["id"]: p for p in list_players()}
        home = players.get(home_id)
        away = players.get(away_id)
        if not home or not away:
            raise ValueError("Player not found.")
        fixtures = [{
            "league_id": league_id,
            "round": 3,
            "match_index": 1,
            "home_player_id": home_id,
            "away_player_id": away_id,
            "home_club_name": home["club_name"],
            "home_ign": home["ign"],
            "away_club_name": away["club_name"],
            "away_ign": away["ign"],
            "leg": 1,  # single leg
        }]
        sb = get_client()
        sb.table("playoff_fixtures").insert(fixtures).execute()
        return len(winners)
    else:
        raise ValueError("Invalid round.")


def get_playoff_winner(league_id: str):
    """Return the winner of the final (round=3), if determined."""
    fixtures = get_playoff_fixtures(league_id)
    final_fixtures = [f for f in fixtures if f["round"] == 3]
    if not final_fixtures:
        return None
    # final is single leg
    f = final_fixtures[0]
    if f["played"]:
        # winner_id is stored in f["winner_id"] if we set it
        # We could compute from score
        if f["home_score"] > f["away_score"]:
            return f["home_player_id"]
        elif f["away_score"] > f["home_score"]:
            return f["away_player_id"]
        else:
            # draw -> maybe penalties? We'll store winner manually
            return None
    return None

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
