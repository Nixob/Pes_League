import streamlit as st
import db
from datetime import date, datetime, time as dtime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

st.set_page_config(page_title="PES with the Bois", layout="wide", initial_sidebar_state="collapsed")

PAGE_LABELS = {
    "home": "Home",
    "fixtures": "Fixtures",
    "table": "League Standing",
    "playoffs": "Playoffs",
    "history": "History",
    "register": "Register",
    "rules": "Rules",
    "admin": "Admin",
}

def player_label(p):
    return f"{p['ign']}  ({p['club_name']})"


# ---------------------------------------------------------------- styling --

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --accent: #B83CF0;
    --accent-soft: rgba(184, 60, 240, 0.12);
    --line: #7d7d84;
    --bg: #0e0e10;
    --card: #17181c;
    --text: #f5f5f7;
    --muted: #9a9aa1;
}

html, body, .stApp { background-color: var(--bg) !important; }
* { font-family: 'Inter', sans-serif; }

/* hide Streamlit chrome we don't want */
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { padding-top: 2.2rem; max-width: 1100px; }

/* --- brand bar --- */
.brand-bar {
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: 1.55rem;
    color: var(--accent);
    letter-spacing: 0.2px;
    text-align: center;
    margin-bottom: 1.6rem;
}

/* --- custom table matching the sketch: thin grey grid, purple header --- */
.league-table-wrap {
    display: flex;
    justify-content: center;
    margin: 1rem 0 2rem 0;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    max-width: 100%;
}
table.league-table {
    border-collapse: collapse;
    min-width: 640px;
    font-family: 'Inter', sans-serif;
    font-size: 0.92rem;
}
table.league-table th, table.league-table td {
    border: 1.5px solid var(--line);
    padding: 10px 16px;
    text-align: center;
    color: var(--text);
    white-space: nowrap;
}
table.league-table td:nth-child(2) {
    text-align: left;
    white-space: normal;
    word-break: break-word;
}
.club-sub {
    display: block;
    font-size: 0.72em;
    color: var(--muted);
    font-weight: 400;
    line-height: 1.3;
}
table.league-table th {
    color: var(--accent);
    font-weight: 600;
    font-family: 'Poppins', sans-serif;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
table.league-table tr:hover td { background-color: var(--accent-soft); }
table.league-table td.rank { color: var(--accent); font-weight: 600; }
table.league-table tr.playoff-row td:first-child {
    box-shadow: inset 4px 0 0 #3b82f6;
}
.playoff-marker-legend {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    color: var(--muted);
    font-size: 0.82rem;
    margin: 0.35rem 0 0.8rem 0;
}
.playoff-marker {
    display: inline-block;
    width: 4px;
    height: 18px;
    background: #3b82f6;
    border-radius: 2px;
}
.knockout-title {
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    color: var(--text);
    font-size: 1.2rem;
    margin: 1.5rem 0 0.7rem;
}
.tie-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 0.9rem;
    margin-bottom: 0.8rem;
}
.tie-meta { color: var(--muted); font-size: 0.8rem; }

/* --- BRACKET (round-columns, adapts to any bracket size) --- */
.bracket-wrap {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding: 1rem 0;
}
.bracket-rounds {
    display: flex;
    gap: 28px;
    min-width: 560px;
    padding: 0.5rem;
}
.bracket-round-col {
    display: flex;
    flex-direction: column;
    gap: 18px;
    justify-content: center;
    min-width: 190px;
    flex: 1;
}
.bracket-match {
    width: 100%;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 0.5rem 0.7rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    transition: 0.2s;
    text-align: center;
}
.bracket-match:hover {
    border-color: var(--accent);
    transform: scale(1.02);
}
.bracket-match.final {
    border: 2px solid var(--accent);
    box-shadow: 0 0 20px rgba(184,60,240,0.25);
    background: rgba(184,60,240,0.06);
}
.bracket-round {
    color: var(--accent);
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 0.2rem;
}
.bracket-round-heading {
    color: var(--muted);
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    text-align: center;
    margin-bottom: 0.3rem;
}
.bracket-team {
    display: flex;
    justify-content: space-between;
    gap: 0.3rem;
    padding: 0.1rem 0;
    font-size: 0.75rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.bracket-team span { overflow: hidden; text-overflow: ellipsis; }
.bracket-team.winner {
    font-weight: 700;
    color: #4ade80;
}
.bracket-agg-mini {
    border-top: 1px solid rgba(125,125,132,0.3);
    margin-top: 0.2rem;
    padding-top: 0.2rem;
    color: var(--muted);
    font-size: 0.55rem;
    text-align: center;
}
.bracket-final-score {
    margin-top: 0.3rem;
    font-weight: 700;
    font-size: 0.75rem;
    color: #facc15;
}
.bracket-pending { opacity: 0.6; }

@media (max-width: 640px) {
    .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
    .brand-bar { font-size: 1.25rem; }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div { font-size: 1.4rem; }

    table.league-table { min-width: 0; width: 100%; font-size: 0.66rem; }
    table.league-table th, table.league-table td { padding: 4px 5px; }
    .club-sub { font-size: 0.78em; }

    .bracket-rounds {
        min-width: 480px;
        gap: 16px;
        padding: 0.2rem;
    }
    .bracket-round-col { min-width: 150px; gap: 12px; }
    .bracket-match { padding: 0.3rem 0.4rem; }
    .bracket-team { font-size: 0.6rem; }
    .bracket-round { font-size: 0.5rem; }
    .bracket-agg-mini { font-size: 0.48rem; }
    .bracket-final-score { font-size: 0.6rem; }
}

/* --- section headings --- */
h1, h2, h3 { font-family: 'Poppins', sans-serif !important; color: var(--text) !important; }
.section-title {
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    color: var(--text);
    font-size: 1.1rem;
    margin: 1.6rem 0 0.6rem 0;
}
.muted { color: var(--muted); font-size: 0.9rem; }

/* --- buttons --- */
.stButton > button {
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}
.stButton > button[kind="primary"] {
    background-color: var(--accent);
    border: none;
}
.stButton > button {
    padding: 0.6rem 1rem;
    font-size: 1rem;
}

/* --- bigger toast popups --- */
div[data-testid="stToast"] {
    font-size: 1.15rem;
    padding: 1rem 1.3rem;
    min-width: 320px;
}
div[data-testid="stToast"] p {
    font-size: 1.1rem !important;
}
div[data-testid="stToast"] svg {
    width: 1.4rem;
    height: 1.4rem;
}

/* --- big centered loading overlay for full-page reruns --- */
div[data-testid="stStatusWidget"] {
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) scale(2.4) !important;
    z-index: 9999 !important;
    background: rgba(14, 14, 16, 0.92) !important;
    padding: 1.1rem 1.5rem !important;
    border-radius: 14px !important;
    border: 1.5px solid var(--accent) !important;
    box-shadow: 0 6px 28px rgba(0, 0, 0, 0.5) !important;
}
</style>
""", unsafe_allow_html=True)


def render_table(rows: list[dict], marker_count: int = 0):
    """Renders a list of dicts as the sketch-style bordered table. The
    first `marker_count` rows get the blue playoff-qualification stripe;
    pass 0 to disable it entirely."""
    if not rows:
        st.markdown('<p class="muted">No results yet.</p>', unsafe_allow_html=True)
        return
    cols = list(rows[0].keys())
    html = ['<div class="league-table-wrap"><table class="league-table"><thead><tr>']
    for c in cols:
        html.append(f"<th>{c}</th>")
    html.append("</tr></thead><tbody>")
    for row_index, r in enumerate(rows):
        row_class = ' class="playoff-row"' if row_index < marker_count else ''
        html.append(f"<tr{row_class}>")
        for i, c in enumerate(cols):
            cls = ' class="rank"' if i == 0 else ""
            html.append(f"<td{cls}>{r[c]}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def standings_rows(table):
    return [{
        "#": i + 1,
        "Player": f"{r['club_name']}<span class='club-sub'>{r['ign']}</span>",
        "P": r["played"], "W": r["won"], "D": r["drawn"], "L": r["lost"],
        "GF": r["gf"], "GA": r["ga"], "GD": r["gd"], "Pts": r["points"],
    } for i, r in enumerate(table)]


def render_undo_control(fixture_id: str, key_prefix: str) -> bool:
    """Renders an 'Undo' button with a Yes/Cancel confirmation step for a
    played fixture, sharing the pattern used on the Fixtures page, the
    playoff tie editor, and the final. Returns True the instant the result
    is actually undone, so the caller can toast / rerun as needed."""
    confirm_key = f"{key_prefix}_undo_confirm_{fixture_id}"
    c1, c2 = st.columns([3, 1])
    if st.session_state.get(confirm_key):
        c1.markdown('<p class="muted">Undo this result?</p>', unsafe_allow_html=True)
        if c2.button("Yes, undo", key=f"{key_prefix}_undo_yes_{fixture_id}", use_container_width=True):
            db.unmark_result(fixture_id)
            st.session_state[confirm_key] = False
            return True
        if c2.button("Cancel", key=f"{key_prefix}_undo_no_{fixture_id}", use_container_width=True):
            st.session_state[confirm_key] = False
    else:
        if c2.button("Undo", key=f"{key_prefix}_undo_{fixture_id}", use_container_width=True):
            st.session_state[confirm_key] = True
    return False


def render_score_entry(fixture_id: str, key_prefix: str, home_label: str, away_label: str, button_label: str = "Save") -> bool:
    """Renders the paired home/away number inputs + save button used to
    submit a result, shared across the Fixtures page, playoff tie editor,
    and the final. Returns True the instant a result is saved."""
    c1, c2, c3 = st.columns([1, 1, 1.4])
    hs = c1.number_input(home_label, min_value=0, max_value=20, step=1, key=f"{key_prefix}_hs_{fixture_id}")
    aws = c2.number_input(away_label, min_value=0, max_value=20, step=1, key=f"{key_prefix}_as_{fixture_id}")
    c3.markdown("<div style='height: 1.6rem'></div>", unsafe_allow_html=True)
    if c3.button(button_label, key=f"{key_prefix}_tick_{fixture_id}", use_container_width=True):
        try:
            db.submit_result(fixture_id, int(hs), int(aws))
            return True
        except Exception as e:
            st.error(str(e))
    return False


# --------------------------------------------------------------------- UI --

st.markdown('<div class="brand-bar">PES with the Bois</div>', unsafe_allow_html=True)


def go_to(page: str):
    st.query_params["page"] = page


if "page" not in st.query_params:
    st.query_params["page"] = "home"

page_key = st.query_params.get("page", "home")
if page_key not in PAGE_LABELS:
    page_key = "home"

if page_key != "home":
    st.button("← Home", key="home_link", on_click=go_to, args=("home",))


def leg_deadline_passed(league, leg: int) -> bool:
    """A leg's deadline is 7:30 AM IST on the given date — not the day
    after. Once that moment passes, the leg is considered closed."""
    raw = league.get("deadline") if leg == 1 else league.get("leg2_deadline")
    if not raw:
        return False
    deadline_dt = datetime.combine(date.fromisoformat(raw), dtime(7, 30), tzinfo=IST)
    return datetime.now(IST) >= deadline_dt


# ---------------------------------------------------------- playoff rounds --
# Knockout rounds are configurable (2/4/8 qualifiers, single-match or
# two-legged), so all of this is written to adapt to whatever the admin
# picked when playoffs were created, rather than assuming a fixed top-8
# two-legged bracket.

ROUND_LEGS = {
    "qf": (db.QF_LEG1, db.QF_LEG2),
    "sf": (db.SF_LEG1, db.SF_LEG2),
    "final": (db.FINAL_LEG, None),
}
ROUND_TITLES = {"qf": "Quarter Final", "sf": "Semi Final", "final": "Final"}
ROUND_DEADLINE_COL = {"qf": "qf_deadline", "sf": "sf_deadline", "final": "final_deadline"}


def rounds_for_size(size: int) -> list[str]:
    """Which round keys this bracket size actually has, in order."""
    if size == 8:
        return ["qf", "sf", "final"]
    if size == 4:
        return ["sf", "final"]
    return ["final"]


def round_deadline_passed(league, round_key: str) -> bool:
    """Same 7:30 AM IST cutoff rule as the league-stage deadlines,
    applied to one knockout round's deadline."""
    raw = league.get(ROUND_DEADLINE_COL[round_key])
    if not raw:
        return False
    deadline_dt = datetime.combine(date.fromisoformat(raw), dtime(7, 30), tzinfo=IST)
    return datetime.now(IST) >= deadline_dt


def grouped_ties(fixtures, leg1_no, leg2_no):
    """Group a round's fixtures into ties by the two player IDs involved.
    Under two-legged format each group has 2 fixtures (leg1 + leg2);
    under single-match format (or the final, which is always single)
    each group naturally has just 1. Deterministic order based on the
    fixture creation order supplied by the database."""
    groups = {}
    order = []
    for f in fixtures:
        if f["leg"] not in (leg1_no, leg2_no):
            continue
        key = tuple(sorted((f["home_player_id"], f["away_player_id"])))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(f)
    return [groups[k] for k in order]


def tie_data(tie, seeds):
    """Returns (home_id, away_id, home_ign, away_ign, score_str, winner,
    reason) for a tie of 1 or 2 fixtures. Mirrors db._tie_winner's logic
    so the display always agrees with what actually decides the tie."""
    if not tie:
        return (None, None, "TBD", "TBD", "–", None, None)
    f1 = tie[0]
    a, b = f1["home_player_id"], f1["away_player_id"]

    if len(tie) == 1:
        played = f1["played"]
        score_str = f'{f1["home_score"]} – {f1["away_score"]}' if played else "–"
        winner, reason = None, None
        if played:
            if f1["home_score"] != f1["away_score"]:
                winner = a if f1["home_score"] > f1["away_score"] else b
                reason = "result"
            else:
                winner = min((a, b), key=lambda pid: seeds.get(pid, 999))
                reason = "higher league seed"
        return (a, b, f1["home_ign"], f1["away_ign"], score_str, winner, reason)

    # two-legged tie
    f2 = tie[1]
    agg = {a: 0, b: 0}
    away = {a: 0, b: 0}
    for f in tie:
        if f["played"]:
            agg[f["home_player_id"]] += f["home_score"]
            agg[f["away_player_id"]] += f["away_score"]
            away[f["away_player_id"]] += f["away_score"]
    both_played = all(f["played"] for f in tie)
    score_str = f'{agg[a]} – {agg[b]}' if any(f["played"] for f in tie) else "–"
    winner, reason = None, None
    if both_played:
        if agg[a] != agg[b]:
            winner, reason = (a if agg[a] > agg[b] else b), "aggregate"
        elif away[a] != away[b]:
            winner, reason = (a if away[a] > away[b] else b), "away goals"
        else:
            winner, reason = min((a, b), key=lambda pid: seeds.get(pid, 999)), "higher league seed"
    return (a, b, f1["home_ign"], f1["away_ign"], score_str, winner, reason)


def maybe_auto_resolve():
    """Runs on every page load. If a league-stage leg's deadline has
    passed and it still has unplayed fixtures, auto-resolves them (see
    auto_resolve_leg) and lets the admin know via a toast. Cheap no-op
    once everything's already resolved, so it's safe to call
    unconditionally like this. Playoff rounds are NOT auto-resolved —
    an overdue tie needs the admin to pick a winner on the Admin page,
    which then applies as a forfeit."""
    league = db.get_active_league()
    if not league:
        return
    for leg in (1, 2):
        if leg_deadline_passed(league, leg):
            resolved = db.auto_resolve_leg(league["id"], leg)
            if resolved:
                st.toast(f"Auto-resolved {resolved} overdue Leg {leg} fixture(s).")


maybe_auto_resolve()


def render_playoff_bracket(league):
    """Renders the knockout bracket visual and round-by-round match
    editors for the given league, adapting to whatever qualifier count
    and format (single-match / two-legged) were picked when playoffs
    were created. Shared by the live Playoffs page (editable while the
    league is still active -- every editor inside is gated on
    league.get('status') == 'active') and by History, which calls this
    read-only for each completed league so its bracket stays viewable
    after a new league starts."""
    if league.get("status") == "active":
        db.advance_playoffs(league["id"])

    size = db.get_playoff_size(league["id"])
    fmt = db.get_playoff_format(league["id"])
    rounds = rounds_for_size(size)

    fmt_label = "Single match" if fmt == "single" else "Two-legged"
    st.markdown(
        f'<p class="muted" style="text-align:center;">Top {size} knockout • {fmt_label} ties</p>',
        unsafe_allow_html=True,
    )
    if fmt == "two_leg":
        st.markdown(
            '<p class="muted" style="text-align:center; font-size:0.85rem;">'
            'In two‑legged ties, the <strong>first leg</strong> is at the home of the <strong>first</strong> team listed; '
            'the <strong>second leg</strong> at the home of the <strong>second</strong> team listed.</p>',
            unsafe_allow_html=True
        )

    fixtures = db.list_fixtures(league["id"])
    seeds = {r["player_id"]: i + 1 for i, r in enumerate(db.get_standings(league["id"])[:size])}

    round_groups = {}
    for rk in rounds:
        leg1, leg2 = ROUND_LEGS[rk]
        round_groups[rk] = grouped_ties(fixtures, leg1, leg2 if leg2 else leg1)

    if not any(round_groups.values()):
        st.info(f"The top {size} playoff bracket will appear here once the league stage is completed.")
        return

    # --- deadline status lines, one per applicable round ---
    for rk in rounds:
        raw = league.get(ROUND_DEADLINE_COL[rk])
        if not raw:
            continue
        d = date.fromisoformat(raw)
        title = ROUND_TITLES[rk]
        if round_deadline_passed(league, rk):
            st.markdown(
                f'<p class="muted" style="text-align:center;">{title} deadline was '
                f'<b>{d.strftime("%d %b %Y")}, 7:30 AM</b> — any tie still undecided was settled by admin forfeit.</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<p class="muted" style="text-align:center;">{title} deadline: '
                f'<b>{d.strftime("%d %b %Y")}, 7:30 AM</b></p>',
                unsafe_allow_html=True,
            )

    # --- bracket visual: one column per round ---
    def match_html(tie, round_label, is_final=False):
        cls = "bracket-match final" if is_final else "bracket-match"
        if not tie:
            pending_cls = cls + " bracket-pending"
            return (f'<div class="{pending_cls}"><div class="bracket-round">{round_label}</div>'
                     f'<div class="bracket-team"><span>—</span></div><div class="bracket-team"><span>—</span></div></div>')
        a, b, n1, n2, score, winner, reason = tie_data(tie, seeds)
        w1 = ' winner' if winner and winner == a else ''
        w2 = ' winner' if winner and winner == b else ''
        score_block = (f'<div class="bracket-final-score">{score}</div>' if is_final
                        else f'<div class="bracket-agg-mini">{"Agg" if len(tie) == 2 else "Score"} {score}</div>')
        return f'''<div class="{cls}">
            <div class="bracket-round">{round_label}</div>
            <div class="bracket-team{w1}"><span>{n1}</span></div>
            <div class="bracket-team{w2}"><span>{n2}</span></div>
            {score_block}
        </div>'''

    cols_html = []
    for rk in rounds:
        ties = round_groups[rk]
        heading = ROUND_TITLES[rk]
        cards = "".join(
            match_html(tie, f"{heading} {i}" if len(ties) > 1 else heading, is_final=(rk == "final"))
            for i, tie in enumerate(ties, 1)
        ) if ties else match_html(None, heading, is_final=(rk == "final"))
        cols_html.append(f'<div class="bracket-round-col"><div class="bracket-round-heading">{heading}</div>{cards}</div>')

    st.markdown(f'<div class="bracket-wrap"><div class="bracket-rounds">{"".join(cols_html)}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="knockout-title">Match results</div>', unsafe_allow_html=True)

    def render_tie_editor(tie, title, round_key):
        leg1_no, leg2_no = ROUND_LEGS[round_key]
        a, b, n1, n2, score, winner, reason = tie_data(tie, seeds)
        # A tie is "locked" once ITS OWN winner has actually been placed
        # into the next round.
        next_idx = rounds.index(round_key) + 1
        next_round_fixtures = fixtures if next_idx >= len(rounds) else [
            f for f in fixtures if f["leg"] in ROUND_LEGS[rounds[next_idx]]
        ]
        round_has_next = db.tie_has_advanced(winner, next_round_fixtures) if next_idx < len(rounds) else False

        with st.container(border=True):
            st.markdown(f"**{title}** — {n1} vs {n2}")
            for i, f in enumerate(tie):
                label = f"Leg {i + 1}" if len(tie) == 2 else "Match"
                home_label = f"{f['home_ign']} (H)"
                away_label = f"{f['away_ign']} (A)"
                if f["played"]:
                    tag = "  ·  Forfeit" if f.get("forfeit") else ""
                    st.markdown(f"**{label}:** {home_label} vs {away_label} — :green[**{f['home_score']} – {f['away_score']}**]{tag}")
                    if not round_has_next and league.get("status") == "active":
                        if render_undo_control(f["id"], "po"):
                            st.rerun()
                    elif round_has_next:
                        st.caption("Advanced to the next round")
                elif league.get("status") == "active":
                    if render_score_entry(f["id"], "po", f"{label} {home_label}", f"{label} {away_label}", f"Save {label}"):
                        st.rerun()
            if len(tie) == 2:
                agg = {a: 0, b: 0}
                away = {a: 0, b: 0}
                for f in tie:
                    if f["played"]:
                        agg[f["home_player_id"]] += f["home_score"]
                        agg[f["away_player_id"]] += f["away_score"]
                        away[f["away_player_id"]] += f["away_score"]
                st.caption(f"Aggregate: {agg[a]} – {agg[b]}  •  Away goals: {away[a]} – {away[b]}")
            if winner:
                win_name = n1 if winner == a else n2
                st.success(f"{win_name} advances ({reason}).")

    round_done = {
        rk: bool(round_groups[rk]) and all(tie_data(t, seeds)[5] for t in round_groups[rk])
        for rk in rounds
    }
    tab_labels = []
    for rk in rounds:
        if round_groups[rk]:
            tab_labels.append(f"{ROUND_TITLES[rk]}{' (complete)' if round_done[rk] else ''}")
        else:
            tab_labels.append(f"{ROUND_TITLES[rk]} (locked)")
    tabs = st.tabs(tab_labels)

    for rk, tab in zip(rounds, tabs):
        with tab:
            ties = round_groups[rk]
            if not ties:
                st.markdown(f'<p class="muted">{ROUND_TITLES[rk]} unlocks once the previous round is decided.</p>', unsafe_allow_html=True)
                continue
            for i, tie in enumerate(ties, 1):
                title = f"{ROUND_TITLES[rk]} {i}" if len(ties) > 1 else ROUND_TITLES[rk]
                render_tie_editor(tie, title, rk)
            if rk == "final":
                champion = db.playoff_champion(league["id"])
                if champion:
                    players = {p["id"]: p for p in db.list_players()}
                    winner = players.get(champion)
                    winner_name = f"{winner['ign']} ({winner['club_name']})" if winner else "Champion"
                    st.success(f"Champion: {winner_name}")


# ---------------------------------------------------------------------- Home --
if page_key == "home":
    st.markdown('<div style="height: 0.8rem;"></div>', unsafe_allow_html=True)

    tile_rows = [["fixtures", "table"], ["playoffs", "history"], ["register", "rules"], ["admin"]]
    for row in tile_rows:
        cols = st.columns(len(row)) if len(row) > 1 else [st.columns([1, 2, 1])[1]]
        for i, key in enumerate(row):
            with cols[i]:
                with st.container(border=True):
                    st.button(
                        PAGE_LABELS[key], key=f"tile_{key}",
                        use_container_width=True, on_click=go_to, args=(key,),
                    )


# ------------------------------------------------------------------ Fixtures --
elif page_key == "fixtures":
    league = db.get_active_league()

    if not league:
        st.info("No active league right now. An admin needs to start one.")
    else:
        st.markdown(f'<div class="section-title">{league["name"]}</div>', unsafe_allow_html=True)
        # This page is for the league stage only; knockout matches live on Playoffs.
        fixtures = [f for f in db.list_fixtures(league["id"]) if f["leg"] in (1, 2)]

        leg1_closed = leg_deadline_passed(league, 1)
        leg2_closed = leg_deadline_passed(league, 2)

        raw_deadline = league.get("deadline")
        if raw_deadline:
            deadline_date = date.fromisoformat(raw_deadline)
            if leg1_closed:
                st.markdown(
                    f'<p class="muted">Leg 1 deadline was <b>{deadline_date.strftime("%d %b %Y")}, 7:30 AM</b> — '
                    f'Leg 1 is now closed, results can only be corrected by the admin.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<p class="muted">Leg 1 deadline: <b>{deadline_date.strftime("%d %b %Y")}, 7:30 AM</b></p>', unsafe_allow_html=True)

        raw_leg2_deadline = league.get("leg2_deadline")
        if raw_leg2_deadline:
            leg2_deadline_date = date.fromisoformat(raw_leg2_deadline)
            if leg2_closed:
                st.markdown(
                    f'<p class="muted">Leg 2 deadline was <b>{leg2_deadline_date.strftime("%d %b %Y")}, 7:30 AM</b> — '
                    f'Leg 2 is now closed, results can only be corrected by the admin.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<p class="muted">Leg 2 deadline: <b>{leg2_deadline_date.strftime("%d %b %Y")}, 7:30 AM</b></p>', unsafe_allow_html=True)

        approved_players = [p for p in db.list_players(status="approved") if p["active"]]
        names = {p["id"]: player_label(p) for p in approved_players}
        me = st.selectbox(
            "I am...", options=[None] + list(names.keys()),
            format_func=lambda pid: "— select your name —" if pid is None else names[pid],
        )

        if not league["leg2_unlocked"]:
            st.markdown(
                '<p class="muted">Leg 2 fixtures are locked until the admin opens them '
                '(once every Leg 1 match is played).</p>',
                unsafe_allow_html=True,
            )

        active_leg_label = "Leg 2" if league["leg2_unlocked"] else "Leg 1"
        leg_options = ["All", "Leg 1", "Leg 2"]
        leg_filter = st.radio(
            "View", options=leg_options, index=leg_options.index(active_leg_label),
            horizontal=True, label_visibility="collapsed",
        )

        st.markdown('<div class="section-title">Fixture list</div>', unsafe_allow_html=True)
        st.markdown('<p class="muted">Tick a fixture once it\'s been played and enter the score.</p>', unsafe_allow_html=True)

        if me:
            show_all = st.checkbox("Show everyone's fixtures instead of just mine")
            visible_fixtures = fixtures if show_all else [
                f for f in fixtures if me in (f["home_player_id"], f["away_player_id"])
            ]
        else:
            visible_fixtures = fixtures

        if leg_filter != "All":
            wanted_leg = 1 if leg_filter == "Leg 1" else 2
            visible_fixtures = [f for f in visible_fixtures if f["leg"] == wanted_leg]

        @st.fragment
        def render_fixture_card(fixture_id: str, leg2_unlocked: bool, leg_closed: bool, playoffs_locked: bool):
            f = db.get_fixture(fixture_id)
            if f is None:
                return
            locked = leg_closed or playoffs_locked
            with st.container(border=True):
                leg_tag = f"Leg {f['leg']}"
                if f["played"] and f.get("forfeit"):
                    leg_tag += "  ·  Forfeit"
                elif not f["played"] and leg_closed:
                    leg_tag += "  ·  Overdue"
                st.markdown(
                    f"**{f['home_ign']}** _{f['home_club_name']}_ &nbsp;vs&nbsp; "
                    f"**{f['away_ign']}** _{f['away_club_name']}_"
                    f"  \n<span class='muted' style='font-size:0.78rem;'>{leg_tag}</span>",
                    unsafe_allow_html=True,
                )
                if f["played"]:
                    st.markdown(f":green[**{f['home_score']} – {f['away_score']}**]")
                    if locked:
                        reason = "Leg closed" if leg_closed else "Playoffs have started"
                        st.markdown(f'<p class="muted">{reason} — only the admin can change this now.</p>', unsafe_allow_html=True)
                    elif render_undo_control(f["id"], "fx"):
                        st.toast("Result undone.")
                elif f["leg"] == 2 and not leg2_unlocked:
                    st.markdown('<p class="muted">Locked until Leg 1 is complete.</p>', unsafe_allow_html=True)
                elif playoffs_locked:
                    st.markdown('<p class="muted">Playoffs have started — league results are now locked. Contact the admin for corrections.</p>', unsafe_allow_html=True)
                elif leg_closed:
                    st.markdown('<p class="muted">Leg closed — this will be auto-resolved shortly, or fixed by the admin.</p>', unsafe_allow_html=True)
                else:
                    if render_score_entry(f["id"], "fx", "Home", "Away", "Played"):
                        st.toast("Result saved")


        playoffs_locked = db.playoffs_started(league["id"])
        for f in visible_fixtures:
            fixture_leg_closed = leg1_closed if f["leg"] == 1 else leg2_closed
            render_fixture_card(f["id"], league["leg2_unlocked"], fixture_leg_closed, playoffs_locked)


# --------------------------------------------------------------------- Table --
elif page_key == "table":
    league = db.get_active_league()

    if not league:
        st.info("No active league right now.")
    else:
        st.markdown(f'<p class="muted" style="text-align:center;">{league["name"]}</p>', unsafe_allow_html=True)
        table = db.get_standings(league["id"])
        playoffs_on = db.playoffs_started(league["id"])
        marker_n = db.get_playoff_size(league["id"]) if playoffs_on else 0
        if marker_n and len(table) >= marker_n:
            st.markdown(
                f'<div class="playoff-marker-legend"><span class="playoff-marker"></span> Top {marker_n} — playoff qualification</div>',
                unsafe_allow_html=True,
            )
        render_table(standings_rows(table), marker_count=marker_n)


elif page_key == "playoffs":
    league = db.get_active_league()
    if not league:
        completed = db.list_completed_leagues()
        league = completed[0] if completed else None

    if not league:
        st.info("No league or playoff bracket exists yet.")
    else:
        st.markdown(f'<p class="muted" style="text-align:center;">{league["name"]}</p>', unsafe_allow_html=True)
        render_playoff_bracket(league)


# ------------------------------------------------------------------- History --
elif page_key == "history":
    completed = db.list_completed_leagues()
    if not completed:
        st.markdown('<p class="muted">No completed leagues yet — first champion is still TBD.</p>', unsafe_allow_html=True)
    else:
        for lg in completed:
            winner = lg.get("winner")
            winner_str = f"{winner['ign']} ({winner['club_name']})" if winner else "—"
            with st.expander(f"{lg['name']} — winner: {winner_str}"):
                table = db.get_standings(lg["id"])
                marker_n = db.get_playoff_size(lg["id"]) if db.playoffs_started(lg["id"]) else 0
                render_table(standings_rows(table), marker_count=marker_n)
                if db.playoffs_started(lg["id"]):
                    st.markdown('<div class="knockout-title">Playoff bracket</div>', unsafe_allow_html=True)
                    render_playoff_bracket(lg)



# ------------------------------------------------------------------ Register --
elif page_key == "register":
    st.markdown('<div class="section-title">Join the league</div>', unsafe_allow_html=True)
    st.markdown('<p class="muted">Enter your club name and in-game name. The admin will approve you before you show up in fixtures.</p>', unsafe_allow_html=True)

    with st.form("register_form", clear_on_submit=True):
        club_name = st.text_input("Club name")
        ign = st.text_input("In-game name (IGN)")
        submitted = st.form_submit_button("Submit for approval", type="primary")
        if submitted:
            if not club_name or not ign:
                st.error("Both fields are required.")
            else:
                try:
                    db.register_player(club_name, ign)
                    st.success("Submitted! Waiting on admin approval.")
                except Exception as e:
                    st.error(str(e))

    st.markdown('<div class="section-title">Approved players</div>', unsafe_allow_html=True)
    approved = db.list_players(status="approved")
    render_table([{"Club": p["club_name"], "IGN": p["ign"], "Active": "Yes" if p["active"] else "No"} for p in approved])


# --------------------------------------------------------------------- Rules --
elif page_key == "rules":
    st.markdown('<div class="section-title">How this works</div>', unsafe_allow_html=True)
    st.markdown("""
1. **Register** — enter your club name and IGN, wait for admin approval.
2. **Check Fixtures** — you don't have to play in order, any fixture on your list can be played whenever.
3. **After a match, update the score from the Fixtures page** — find your name and your opponent's name, put in the scores, and click **Played**.
4. **In-game rules** — keep Extra Time and Penalties turned OFF for league matches.
5. **Playoffs** — however many players the admin sets qualify (2, 4, or 8), seeded from the league table, in either two-legged Home & Away ties or single-match knockout, right through to the final.
6. **Away goals** — in a two-legged tie level on aggregate, the team with more away goals advances. If that's level too (or a single-match tie ends level), the higher league seed advances.
""")


# --------------------------------------------------------------------- Admin --
elif page_key == "admin":
    pw = st.text_input("Admin password", type="password")
    if pw != st.secrets.get("ADMIN_PASSWORD", ""):
        st.warning("Enter the admin password to continue.")
        st.stop()

    st.success("Logged in as admin.")
    admin_active_league = db.get_active_league()
    admin_playoffs_started = bool(admin_active_league and db.playoffs_started(admin_active_league["id"]))

    st.markdown('<div class="section-title">Pending approvals</div>', unsafe_allow_html=True)
    pending = db.list_players(status="pending")
    if not pending:
        st.markdown('<p class="muted">Nothing pending.</p>', unsafe_allow_html=True)
    else:
        for p in pending:
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(f"{p['ign']} — {p['club_name']}")
            if c2.button("Approve", key=f"appr_{p['id']}"):
                try:
                    db.approve_player(p["id"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
            if c3.button("Reject", key=f"rej_{p['id']}"):
                db.reject_player(p["id"])
                st.rerun()

    st.markdown(f'<div class="section-title">All players ({db.player_count()}/{db.MAX_PLAYERS} approved)</div>', unsafe_allow_html=True)
    st.markdown('<p class="muted">Removing a player deletes them from the list, but past match history keeps their name — old tables aren\'t affected.</p>', unsafe_allow_html=True)
    all_players = db.list_players()
    for p in all_players:
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
        c1.write(f"**{p['ign']}** ({p['club_name']})")
        c2.write(f"status: {p['status']}")
        active = c3.checkbox("Active", value=p["active"], key=f"active_{p['id']}")
        if active != p["active"]:
            db.update_player(p["id"], p["club_name"], p["ign"], active)
            st.rerun()
        if c4.button("Remove", key=f"rm_{p['id']}", disabled=admin_playoffs_started):
            try:
                db.remove_player(p["id"])
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.markdown('<div class="section-title">Add a player directly</div>', unsafe_allow_html=True)
    with st.form("admin_add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        club = c1.text_input("Club name")
        ign = c2.text_input("IGN")
        if st.form_submit_button("Add", type="primary"):
            try:
                db.admin_add_player(club, ign)
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.markdown('<div class="section-title">League management</div>', unsafe_allow_html=True)
    active_league = admin_active_league

    if active_league:
        st.write(f"Active league: **{active_league['name']}**")
        playoff_mode = db.playoffs_started(active_league["id"])

        if not playoff_mode:
            st.markdown('<p class="section-title" style="font-size: 1rem;">League deadlines</p>', unsafe_allow_html=True)
            for leg in (1, 2):
                if leg == 1:
                    raw = active_league.get("deadline")
                    current = date.fromisoformat(raw) if raw else None
                    passed = leg_deadline_passed(active_league, 1)
                    label = "Leg 1"
                    input_key = "deadline_input"
                    update_func = db.set_league_deadline
                    clear_func = lambda lid: db.set_league_deadline(lid, None)
                else:
                    raw = active_league.get("leg2_deadline")
                    current = date.fromisoformat(raw) if raw else None
                    passed = leg_deadline_passed(active_league, 2)
                    label = "Leg 2"
                    input_key = "leg2_deadline_admin_input"
                    update_func = db.set_league_leg2_deadline
                    clear_func = lambda lid: db.set_league_leg2_deadline(lid, None)

                if current:
                    status = "passed — overdue fixtures were auto-resolved" if passed else "upcoming"
                    st.markdown(f'<p class="muted">{label} deadline: <b>{current.strftime("%d %b %Y")}, 7:30 AM</b> ({status}).</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p class="muted">No {label} deadline set.</p>', unsafe_allow_html=True)

                new_date = st.date_input(f"Set / change {label} deadline", value=current or date.today(), key=f"{input_key}_{leg}")
                col1, col2 = st.columns(2)
                if col1.button(f"Update {label} deadline", key=f"update_deadline_{leg}", use_container_width=True):
                    update_func(active_league["id"], new_date)
                    st.rerun()
                if col2.button(f"Clear {label} deadline", key=f"clear_deadline_{leg}", use_container_width=True, disabled=not current):
                    clear_func(active_league["id"])
                    st.rerun()

            st.markdown('<p class="section-title" style="font-size: 1rem;">Leg 2 lock</p>', unsafe_allow_html=True)
            if active_league["leg2_unlocked"]:
                st.markdown('<p class="muted">Leg 2 is unlocked.</p>', unsafe_allow_html=True)
            else:
                all_leg1_done = db.leg1_complete(active_league["id"])
                fixtures_now = [f for f in db.list_fixtures(active_league["id"]) if f["leg"] in (1, 2)]
                leg1_total = sum(1 for f in fixtures_now if f["leg"] == 1)
                leg1_played = sum(1 for f in fixtures_now if f["leg"] == 1 and f["played"])
                st.markdown(f'<p class="muted">Leg 1 progress: {leg1_played}/{leg1_total} played</p>', unsafe_allow_html=True)
                if st.button("Unlock Leg 2 matches", disabled=not all_leg1_done):
                    db.unlock_leg2(active_league["id"])
                    st.rerun()
                if not all_leg1_done:
                    st.markdown('<p class="muted">Unlock becomes available once every Leg 1 fixture is played (including automatic deadline resolutions).</p>', unsafe_allow_html=True)

            league_done = db.league_stage_complete(active_league["id"])
            table_now = db.get_standings(active_league["id"])
            st.markdown('<p class="section-title" style="font-size: 1rem;">Start playoffs</p>', unsafe_allow_html=True)
            if league_done:
                po_size = st.radio(
                    "How many players qualify for the playoffs?",
                    options=[8, 4, 2],
                    format_func=lambda n: f"Top {n}",
                    horizontal=True,
                    key="playoff_size_choice",
                )
                po_format = st.radio(
                    "Knockout tie format",
                    options=["two_leg", "single"],
                    format_func=lambda v: "Two-legged (Home & Away)" if v == "two_leg" else "Single match",
                    horizontal=True,
                    key="playoff_format_choice",
                )
                if len(table_now) >= po_size:
                    seed_note = {
                        8: "seeded 1v8, 4v5, 2v7, 3v6 into quarter-finals",
                        4: "seeded 1v4, 2v3 straight into semi-finals",
                        2: "seeded 1v2 straight into the final",
                    }[po_size]
                    st.markdown(f'<p class="muted">League stage complete. Top {po_size} will be {seed_note}.</p>', unsafe_allow_html=True)
                    if st.button(f"Create Top {po_size} playoffs", type="primary", use_container_width=True):
                        try:
                            db.create_playoffs(active_league["id"], size=po_size, format=po_format)
                            st.success("League stage locked — playoff bracket created.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                else:
                    st.warning(f"League stage is complete, but only {len(table_now)} teams are in the table. A top-{po_size} bracket needs at least {po_size}.")
            else:
                st.markdown('<p class="muted">Finish every league fixture first. Once all matches are done, playoff options will unlock here.</p>', unsafe_allow_html=True)

            st.markdown('<p class="section-title" style="font-size: 1rem;">Add a player mid-season</p>', unsafe_allow_html=True)
            existing_ids = db.get_league_participant_ids(active_league["id"])
            approved_active = [p for p in db.list_players(status="approved") if p["active"]]
            joinable = [p for p in approved_active if p["id"] not in existing_ids]
            if not joinable:
                st.markdown('<p class="muted">No approved players left to add.</p>', unsafe_allow_html=True)
            elif league_done:
                st.markdown('<p class="muted">Player additions are locked once the league stage is complete.</p>', unsafe_allow_html=True)
            else:
                new_player_id = st.selectbox(
                    "Player to add", options=[p["id"] for p in joinable],
                    format_func=lambda pid: player_label(next(p for p in joinable if p["id"] == pid)),
                )
                if st.button("Add to league"):
                    try:
                        db.add_player_to_league(active_league["id"], new_player_id)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            po_size = db.get_playoff_size(active_league["id"])
            po_format = db.get_playoff_format(active_league["id"])
            fmt_label = "single-match" if po_format == "single" else "two-legged"
            st.success(f"League stage complete — Top {po_size} playoffs ({fmt_label}) are in progress. Rounds advance automatically when each tie is finished.")

            st.markdown('<p class="section-title" style="font-size: 1rem;">Round deadlines</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="muted">Each round has its own optional deadline. Once a round\'s deadline passes, '
                'any tie in it that\'s still undecided shows up below for you to pick who advances — that '
                'applies a forfeit to whichever leg(s) weren\'t played and can be undone from the Playoffs page.</p>',
                unsafe_allow_html=True,
            )

            active_rounds = rounds_for_size(po_size)
            for rk in active_rounds:
                col = ROUND_DEADLINE_COL[rk]
                title = ROUND_TITLES[rk]
                raw = active_league.get(col)
                current = date.fromisoformat(raw) if raw else None
                passed = round_deadline_passed(active_league, rk)
                if current:
                    status = "passed" if passed else "upcoming"
                    st.markdown(f'<p class="muted">{title} deadline: <b>{current.strftime("%d %b %Y")}, 7:30 AM</b> ({status}).</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p class="muted">No {title} deadline set.</p>', unsafe_allow_html=True)

                new_d = st.date_input(f"Set / change {title} deadline", value=current or date.today(), key=f"{rk}_deadline_admin_input")
                dcol1, dcol2 = st.columns(2)
                if dcol1.button(f"Update {title} deadline", key=f"update_{rk}_deadline", use_container_width=True):
                    db.set_round_deadline(active_league["id"], rk, new_d)
                    st.rerun()
                if dcol2.button(f"Clear {title} deadline", key=f"clear_{rk}_deadline", use_container_width=True, disabled=not current):
                    db.set_round_deadline(active_league["id"], rk, None)
                    st.rerun()

            # --- overdue ties needing a forfeit decision ---
            st.markdown('<p class="section-title" style="font-size: 1rem;">Overdue ties</p>', unsafe_allow_html=True)
            fixtures_now = db.list_fixtures(active_league["id"])
            seeds_now = {r["player_id"]: i + 1 for i, r in enumerate(db.get_standings(active_league["id"])[:po_size])}
            players_now = {p["id"]: p for p in db.list_players()}
            any_overdue = False
            for rk in active_rounds:
                if not round_deadline_passed(active_league, rk):
                    continue
                leg1, leg2 = ROUND_LEGS[rk]
                ties = grouped_ties(fixtures_now, leg1, leg2 if leg2 else leg1)
                for i, tie in enumerate(ties, 1):
                    a, b, n1, n2, score, winner, reason = tie_data(tie, seeds_now)
                    if winner:
                        continue
                    any_overdue = True
                    label = f"{ROUND_TITLES[rk]} {i}" if len(ties) > 1 else ROUND_TITLES[rk]
                    with st.container(border=True):
                        st.markdown(f"**{label}** — {n1} vs {n2}  ·  current score: {score}")
                        st.markdown('<p class="muted">Deadline passed — pick who advances. Unplayed leg(s) will be recorded as a forfeit.</p>', unsafe_allow_html=True)
                        fcol1, fcol2 = st.columns(2)
                        if fcol1.button(f"{n1} advances", key=f"forfeit_{rk}_{i}_a", use_container_width=True):
                            db.forfeit_tie_winner(tie, a)
                            st.rerun()
                        if fcol2.button(f"{n2} advances", key=f"forfeit_{rk}_{i}_b", use_container_width=True):
                            db.forfeit_tie_winner(tie, b)
                            st.rerun()
            if not any_overdue:
                st.markdown('<p class="muted">Nothing overdue right now.</p>', unsafe_allow_html=True)

            po = db.list_fixtures(active_league["id"])
            final = next((f for f in po if f["leg"] == db.FINAL_LEG), None)
            champion = db.playoff_champion(active_league["id"])
            if champion:
                winner = players_now.get(champion)
                winner_name = f"{winner['ign']} ({winner['club_name']})" if winner else "Champion"
                st.success(f"{winner_name} has won the season!")
                if st.button("Archive season", type="primary", use_container_width=True):
                    try:
                        db.complete_league(active_league["id"])
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            elif final:
                st.info("The final is ready on the Playoffs page. Enter a winner there; the season will then be ready to archive.")
            else:
                st.info("The knockout bracket is progressing automatically. Open the Playoffs page to enter scores.")

        st.markdown('<p class="section-title" style="font-size: 1rem;">Matches involving removed players</p>', unsafe_allow_html=True)
        st.markdown('<p class="muted">Played matches are kept as history. If a removed player leaves an orphaned fixture, you can delete that individual match.</p>', unsafe_allow_html=True)
        orphaned = db.get_orphaned_fixtures(active_league["id"])
        if not orphaned:
            st.markdown('<p class="muted">None right now.</p>', unsafe_allow_html=True)
        else:
            for f in orphaned:
                score = f"{f['home_score']}-{f['away_score']}" if f["played"] else "unplayed"
                with st.expander(f"{f['home_ign']} vs {f['away_ign']} — {score}"):
                    confirm_del = st.checkbox("Confirm delete — no undo", key=f"confirm_orphan_del_{f['id']}")
                    if st.button("Delete this match", key=f"orphan_del_{f['id']}", disabled=not confirm_del):
                        db.delete_fixture(f["id"])
                        st.rerun()

        st.markdown('<p class="muted">Made a mistake starting this one? Cancel it below instead of archiving it — this deletes the league and all its fixtures with no undo.</p>', unsafe_allow_html=True)
        cancel_confirm = st.checkbox("Confirm cancel — delete this league", key="cancel_active_confirm")
        if st.button("Cancel & delete this league", disabled=not cancel_confirm):
            db.delete_league(active_league["id"])
            st.rerun()
    else:
        st.write("No active league. Start one from approved, active players:")
        approved = [p for p in db.list_players(status="approved") if p["active"]]
        chosen = st.multiselect(
            "Select participants", options=[p["id"] for p in approved],
            format_func=lambda pid: player_label(next(p for p in approved if p["id"] == pid)),
        )
        league_name = st.text_input("League name", value="Season 1")

        set_deadline = st.checkbox("Set a Leg 1 deadline (missed matches auto-resolve)")
        deadline_val = None
        if set_deadline:
            deadline_val = st.date_input("Leg 1 deadline date", min_value=date.today(), key="leg1_deadline_input")

        set_leg2_deadline = st.checkbox("Set a Leg 2 deadline too")
        leg2_deadline_val = None
        if set_leg2_deadline:
            leg2_min = deadline_val if deadline_val else date.today()
            leg2_deadline_val = st.date_input("Leg 2 deadline date", min_value=leg2_min, key="leg2_deadline_input")

        if st.button("Start league", type="primary"):
            if len(chosen) < 2:
                st.error("Pick at least 2 players.")
            else:
                try:
                    db.start_new_league(league_name, chosen, deadline=deadline_val, leg2_deadline=leg2_deadline_val)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))



    st.markdown('<div class="section-title">Delete league history</div>', unsafe_allow_html=True)
    st.markdown('<p class="muted">Permanently deletes a completed league and its fixtures — no undo.</p>', unsafe_allow_html=True)
    completed = db.list_completed_leagues()
    if not completed:
        st.markdown('<p class="muted">No completed leagues to delete.</p>', unsafe_allow_html=True)
    else:
        for lg in completed:
            c1, c2, c3 = st.columns([4, 2, 1])
            c1.write(f"**{lg['name']}**")
            confirm = c2.checkbox("Confirm delete", key=f"confirm_del_{lg['id']}")
            if c3.button("Delete", key=f"del_league_{lg['id']}", disabled=not confirm):
                db.delete_league(lg["id"])
                st.rerun()
