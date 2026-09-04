import streamlit as st
import db
from datetime import date, datetime, time as dtime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

st.set_page_config(page_title="PES with the Bois", page_icon="🟣", layout="wide", initial_sidebar_state="collapsed")

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

PAGE_ICONS = {
    "fixtures": "⚽",
    "table": "🏆",
    "playoffs": "🥇",
    "history": "📜",
    "register": "➕",
    "rules": "📋",
    "admin": "🔐",
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

/* --- page nav dropdown: make the selectbox look like a big heading --- */
div[data-testid="stSelectbox"] {
    max-width: 340px;
    margin: 0 auto 2.2rem auto;
}
div[data-testid="stSelectbox"] label { display: none; }
div[data-testid="stSelectbox"] > div > div {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background-color: transparent !important;
    border: none !important;
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: 1.8rem;
    color: var(--accent) !important;
    justify-content: center;
    text-align: center;
    padding-left: 0;
}
div[data-testid="stSelectbox"] svg { fill: var(--accent) !important; }
div[data-testid="stSelectbox"] input { text-align: center; }

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

/* --- BRACKET (5-column grid, your layout) --- */
.bracket-wrap {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding: 1rem 0;
}
.bracket-board {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
    grid-template-rows: auto auto auto;
    gap: 20px 8px;
    min-width: 640px;
    padding: 0.5rem;
    justify-items: center;
    align-items: center;
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
.bracket-team.winner span::after {
    content: ' 🏆';
    font-size: 0.6rem;
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

/* connectors – simple lines (no arrows) using pseudo-elements */
.bracket-connector {
    position: relative;
}
.bracket-connector::after {
    content: '';
    position: absolute;
    background: var(--line);
}

/* horizontal lines from QF1 to SF1 (row1 col1 to row2 col2) */
.qf1-to-sf1::after {
    right: -16px;
    top: 50%;
    width: 16px;
    height: 2px;
}
/* horizontal from SF1 to Final */
.sf1-to-final::after {
    right: -16px;
    top: 50%;
    width: 16px;
    height: 2px;
}
/* horizontal from Final to SF2 */
.final-to-sf2::after {
    right: -16px;
    top: 50%;
    width: 16px;
    height: 2px;
}
/* horizontal from SF2 to QF3/QF4 */
.sf2-to-qf3::after {
    right: -16px;
    top: 50%;
    width: 16px;
    height: 2px;
}

/* vertical lines from QF1 and QF2 to meet the horizontal before SF1 */
.qf1-to-sf1-vertical::after {
    right: -16px;
    top: 50%;
    width: 2px;
    height: 80px;  /* spans both QF rows */
}

/* Similar for right side */
.qf3-to-sf2-vertical::before {
    left: -16px;
    top: 50%;
    width: 2px;
    height: 80px;
}

/* but we'll use a different approach: we can put connectors in separate cells, but easier: just use a container that spans rows and use borders */

/* I'll simplify: we'll rely on the grid positions and not draw complex lines, just horizontal arrows (optional) */
.bracket-arrow {
    position: relative;
}
.bracket-arrow::after {
    content: '▶';
    position: absolute;
    right: -12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--accent);
    font-size: 0.7rem;
}
.bracket-arrow-left::before {
    content: '◀';
    position: absolute;
    left: -12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--accent);
    font-size: 0.7rem;
}

@media (max-width: 640px) {
    .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
    .brand-bar { font-size: 1.25rem; }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div { font-size: 1.4rem; }

    table.league-table { min-width: 0; width: 100%; font-size: 0.66rem; }
    table.league-table th, table.league-table td { padding: 4px 5px; }
    .club-sub { font-size: 0.78em; }

    .bracket-board {
        min-width: 520px;
        gap: 12px 4px;
        padding: 0.2rem;
    }
    .bracket-match { padding: 0.3rem 0.4rem; }
    .bracket-team { font-size: 0.6rem; }
    .bracket-round { font-size: 0.5rem; }
    .bracket-agg-mini { font-size: 0.48rem; }
    .bracket-final-score { font-size: 0.6rem; }
    .bracket-arrow::after, .bracket-arrow-left::before { font-size: 0.6rem; right: -8px; left: -8px; }
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


def render_table(rows: list[dict], top8_marker: bool = False):
    """Renders a list of dicts as the sketch-style bordered table."""
    if not rows:
        st.markdown('<p class="muted">No results yet.</p>', unsafe_allow_html=True)
        return
    cols = list(rows[0].keys())
    html = ['<div class="league-table-wrap"><table class="league-table"><thead><tr>']
    for c in cols:
        html.append(f"<th>{c}</th>")
    html.append("</tr></thead><tbody>")
    for row_index, r in enumerate(rows):
        row_class = ' class="playoff-row"' if top8_marker and row_index < 8 else ''
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
    """A leg's deadline is 12:00 PM IST on the given date — not the day
    after. Once that moment passes, the leg is considered closed."""
    raw = league.get("deadline") if leg == 1 else league.get("leg2_deadline")
    if not raw:
        return False
    deadline_dt = datetime.combine(date.fromisoformat(raw), dtime(12, 0), tzinfo=IST)
    return datetime.now(IST) >= deadline_dt


def maybe_auto_resolve():
    """Runs on every page load. If a leg's deadline has passed and it
    still has unplayed fixtures, auto-resolves them (see auto_resolve_leg)
    and lets the admin know via a toast. Cheap no-op once everything's
    already resolved, so it's safe to call unconditionally like this."""
    league = db.get_active_league()
    if not league:
        return
    for leg in (1, 2):
        if leg_deadline_passed(league, leg):
            resolved = db.auto_resolve_leg(league["id"], leg)
            if resolved:
                st.toast(f"⏰ Auto-resolved {resolved} overdue Leg {leg} fixture(s).", icon="🤖")


maybe_auto_resolve()


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
                        f"{PAGE_ICONS[key]}  {PAGE_LABELS[key]}", key=f"tile_{key}",
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
                    f'<p class="muted">⏰ Leg 1 deadline was <b>{deadline_date.strftime("%d %b %Y")}, 12:00 PM</b> — '
                    f'Leg 1 is now closed, results can only be corrected by the admin.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<p class="muted">⏳ Leg 1 deadline: <b>{deadline_date.strftime("%d %b %Y")}, 12:00 PM</b></p>', unsafe_allow_html=True)

        raw_leg2_deadline = league.get("leg2_deadline")
        if raw_leg2_deadline:
            leg2_deadline_date = date.fromisoformat(raw_leg2_deadline)
            if leg2_closed:
                st.markdown(
                    f'<p class="muted">⏰ Leg 2 deadline was <b>{leg2_deadline_date.strftime("%d %b %Y")}, 12:00 PM</b> — '
                    f'Leg 2 is now closed, results can only be corrected by the admin.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<p class="muted">⏳ Leg 2 deadline: <b>{leg2_deadline_date.strftime("%d %b %Y")}, 12:00 PM</b></p>', unsafe_allow_html=True)

        approved_players = [p for p in db.list_players(status="approved") if p["active"]]
        names = {p["id"]: player_label(p) for p in approved_players}
        me = st.selectbox(
            "I am...", options=[None] + list(names.keys()),
            format_func=lambda pid: "— select your name —" if pid is None else names[pid],
        )

        if not league["leg2_unlocked"]:
            st.markdown(
                '<p class="muted">🔒 Leg 2 fixtures are locked until the admin opens them '
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
        def render_fixture_card(fixture_id: str, leg2_unlocked: bool, leg_closed: bool):
            f = db.get_fixture(fixture_id)
            if f is None:
                return
            with st.container(border=True):
                leg_tag = f"Leg {f['leg']}"
                if f["played"] and f.get("forfeit"):
                    leg_tag += "  ·  🚩 Forfeit"
                elif not f["played"] and leg_closed:
                    leg_tag += "  ·  ⏰ Overdue"
                st.markdown(
                    f"**{f['home_ign']}** _{f['home_club_name']}_ &nbsp;vs&nbsp; "
                    f"**{f['away_ign']}** _{f['away_club_name']}_"
                    f"  \n<span class='muted' style='font-size:0.78rem;'>{leg_tag}</span>",
                    unsafe_allow_html=True,
                )
                if f["played"]:
                    if leg_closed:
                        st.markdown(f":green[✅ **{f['home_score']} – {f['away_score']}**]")
                        st.markdown('<p class="muted">🔒 Leg closed — only the admin can change this now.</p>', unsafe_allow_html=True)
                    else:
                        confirm_key = f"confirm_undo_{f['id']}"
                        if st.session_state.get(confirm_key):
                            st.markdown(f":green[✅ **{f['home_score']} – {f['away_score']}**]")
                            st.markdown('<p class="muted">Undo this result?</p>', unsafe_allow_html=True)
                            yc, nc = st.columns(2)
                            if yc.button("Yes, undo", key=f"undo_yes_{f['id']}", use_container_width=True):
                                db.unmark_result(f["id"])
                                st.session_state[confirm_key] = False
                                st.toast("Result undone.", icon="↩️")
                            if nc.button("Cancel", key=f"undo_no_{f['id']}", use_container_width=True):
                                st.session_state[confirm_key] = False
                        else:
                            c1, c2 = st.columns([3, 1])
                            c1.markdown(f":green[✅ **{f['home_score']} – {f['away_score']}**]")
                            if c2.button("Undo", key=f"undo_{f['id']}", use_container_width=True):
                                st.session_state[confirm_key] = True
                elif f["leg"] == 2 and not leg2_unlocked:
                    st.markdown('<p class="muted">🔒 Locked until Leg 1 is complete.</p>', unsafe_allow_html=True)
                elif leg_closed:
                    st.markdown('<p class="muted">🔒 Leg closed — this will be auto-resolved shortly, or fixed by the admin.</p>', unsafe_allow_html=True)
                else:
                    c1, c2, c3 = st.columns([1, 1, 1.4])
                    hs = c1.number_input("Home", min_value=0, max_value=20, step=1, key=f"hs_{f['id']}")
                    aws = c2.number_input("Away", min_value=0, max_value=20, step=1, key=f"as_{f['id']}")
                    c3.markdown("<div style='height: 1.6rem'></div>", unsafe_allow_html=True)
                    if c3.button("✅ Played", key=f"tick_{f['id']}", use_container_width=True):
                        db.submit_result(f["id"], int(hs), int(aws))
                        st.toast(f"Result saved — {int(hs)}–{int(aws)}", icon="✅")


        for f in visible_fixtures:
            fixture_leg_closed = leg1_closed if f["leg"] == 1 else leg2_closed
            render_fixture_card(f["id"], league["leg2_unlocked"], fixture_leg_closed)


# --------------------------------------------------------------------- Table --
elif page_key == "table":
    league = db.get_active_league()

    if not league:
        st.info("No active league right now.")
    else:
        st.markdown(f'<p class="muted" style="text-align:center;">{league["name"]}</p>', unsafe_allow_html=True)
        table = db.get_standings(league["id"])
        if len(table) >= 8:
            st.markdown('<div class="playoff-marker-legend"><span class="playoff-marker"></span> Top 8 — playoff qualification</div>', unsafe_allow_html=True)
        render_table(standings_rows(table), top8_marker=True)


# ------------------------------------------------------------------ Playoffs --
elif page_key == "playoffs":
    league = db.get_active_league()
    if not league:
        completed = db.list_completed_leagues()
        league = completed[0] if completed else None

    if not league:
        st.info("No league or playoff bracket exists yet.")
    else:
        if league.get("status") == "active":
            db.advance_playoffs(league["id"])

        fixtures = db.list_fixtures(league["id"])
        qfs = [f for f in fixtures if f["leg"] in (db.QF_LEG1, db.QF_LEG2)]
        sfs = [f for f in fixtures if f["leg"] in (db.SF_LEG1, db.SF_LEG2)]
        final = [f for f in fixtures if f["leg"] == db.FINAL_LEG]

        st.markdown(f'<p class="muted" style="text-align:center;">{league["name"]}</p>', unsafe_allow_html=True)
        st.markdown('<p class="muted" style="text-align:center;">Top 8 knockout • Two-legged ties</p>', unsafe_allow_html=True)

        # Home/away clarification legend
        st.markdown(
            '<p class="muted" style="text-align:center; font-size:0.85rem;">'
            '🏠 In two‑legged ties, the <strong>first leg</strong> is at the home of the <strong>first</strong> team listed; '
            'the <strong>second leg</strong> at the home of the <strong>second</strong> team listed.</p>',
            unsafe_allow_html=True
        )

        def tie_data(tie, leg1_no, leg2_no):
            by_leg = {f["leg"]: f for f in tie}
            if leg1_no not in by_leg or leg2_no not in by_leg:
                return None
            f1, f2 = by_leg[leg1_no], by_leg[leg2_no]
            a, b = f1["home_player_id"], f1["away_player_id"]
            agg = {a: 0, b: 0}
            away = {a: 0, b: 0}
            for f in (f1, f2):
                if f["played"]:
                    agg[f["home_player_id"]] += f["home_score"]
                    agg[f["away_player_id"]] += f["away_score"]
                    away[f["away_player_id"]] += f["away_score"]
            winner = None
            reason = None
            if all(f["played"] for f in (f1, f2)):
                if agg[a] != agg[b]:
                    winner, reason = (a if agg[a] > agg[b] else b), "aggregate"
                elif away[a] != away[b]:
                    winner, reason = (a if away[a] > away[b] else b), "away goals"
                else:
                    seeds = {r["player_id"]: i + 1 for i, r in enumerate(db.get_standings(league["id"])[:8])}
                    winner, reason = min((a, b), key=lambda pid: seeds.get(pid, 99)), "higher league seed"
            return f1, f2, a, b, agg, away, winner, reason

        def grouped_ties(fixtures, leg1_no, leg2_no):
            """Group the two legs of each knockout tie by the two player IDs.
            Always returns groups in deterministic order, based on the fixture
            creation order supplied by the database."""
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

        def tie_label(tie, leg1_no, leg2_no):
            data = tie_data(tie, leg1_no, leg2_no)
            if not data:
                return ("TBD", "TBD", "–", None, None)
            f1, f2, a, b, agg, away, winner, reason = data
            return (
                f1["home_ign"], f1["away_ign"],
                f'{agg[a]} – {agg[b]}' if any(f["played"] for f in (f1, f2)) else "–",
                winner, reason,
            )

        qf_groups = grouped_ties(qfs, db.QF_LEG1, db.QF_LEG2)
        sf_groups = grouped_ties(sfs, db.SF_LEG1, db.SF_LEG2)

        if qf_groups:
            qf_cards=[]
            for i,tie in enumerate(qf_groups,1):
                n1,n2,agg,winner,reason=tie_label(tie,db.QF_LEG1,db.QF_LEG2)
                qf_cards.append((i,n1,n2,agg,winner))
            # Build bracket grid items
            left_qf1 = qf_cards[0] if len(qf_cards) > 0 else None
            left_qf2 = qf_cards[1] if len(qf_cards) > 1 else None
            right_qf1 = qf_cards[2] if len(qf_cards) > 2 else None
            right_qf2 = qf_cards[3] if len(qf_cards) > 3 else None

            # SF and final info
            sf1 = sf_groups[0] if len(sf_groups) > 0 else None
            sf2 = sf_groups[1] if len(sf_groups) > 1 else None
            final_match = final[0] if final else None

            def match_html(card, round_label, winner_class=''):
                if not card:
                    return f'<div class="bracket-match bracket-pending"><div class="bracket-round">{round_label}</div><div class="bracket-team"><span>—</span></div><div class="bracket-team"><span>—</span></div></div>'
                i, n1, n2, agg, winner = card
                w1 = ' winner' if winner and winner == n1 else ''
                w2 = ' winner' if winner and winner == n2 else ''
                return f'''<div class="bracket-match {winner_class}">
                    <div class="bracket-round">{round_label}</div>
                    <div class="bracket-team{w1}"><span>{n1}</span></div>
                    <div class="bracket-team{w2}"><span>{n2}</span></div>
                    <div class="bracket-agg-mini">Agg {agg}</div>
                </div>'''

            # Build SF cards
            if sf1:
                n1,n2,agg,winner,reason = tie_label(sf1, db.SF_LEG1, db.SF_LEG2)
                sf1_html = f'''<div class="bracket-match"><div class="bracket-round">SF 1</div>
                    <div class="bracket-team{' winner' if winner and winner==sf1[0]['home_player_id'] else ''}"><span>{n1}</span></div>
                    <div class="bracket-team{' winner' if winner and winner==sf1[0]['away_player_id'] else ''}"><span>{n2}</span></div>
                    <div class="bracket-agg-mini">Agg {agg}</div></div>'''
            else:
                sf1_html = '<div class="bracket-match bracket-pending"><div class="bracket-round">SF 1</div><div class="bracket-team"><span>Winner QF1</span></div><div class="bracket-team"><span>Winner QF2</span></div></div>'

            if sf2:
                n1,n2,agg,winner,reason = tie_label(sf2, db.SF_LEG1, db.SF_LEG2)
                sf2_html = f'''<div class="bracket-match"><div class="bracket-round">SF 2</div>
                    <div class="bracket-team{' winner' if winner and winner==sf2[0]['home_player_id'] else ''}"><span>{n1}</span></div>
                    <div class="bracket-team{' winner' if winner and winner==sf2[0]['away_player_id'] else ''}"><span>{n2}</span></div>
                    <div class="bracket-agg-mini">Agg {agg}</div></div>'''
            else:
                sf2_html = '<div class="bracket-match bracket-pending"><div class="bracket-round">SF 2</div><div class="bracket-team"><span>Winner QF3</span></div><div class="bracket-team"><span>Winner QF4</span></div></div>'

            # Final
            if final_match:
                final_html = f'''<div class="bracket-match final"><div class="bracket-round">🏆 FINAL</div>
                    <div class="bracket-team"><span>{final_match['home_ign']}</span></div>
                    <div class="bracket-team"><span>{final_match['away_ign']}</span></div>
                    <div class="bracket-final-score">{final_match['home_score']} – {final_match['away_score']}</div></div>'''
            else:
                final_html = '<div class="bracket-match final bracket-pending"><div class="bracket-round">🏆 FINAL</div><div class="bracket-team"><span>Winner SF1</span></div><div class="bracket-team"><span>Winner SF2</span></div><div class="bracket-final-score">FINAL AWAITS</div></div>'

            # Build the 5-column grid with explicit row/column placement
            # We'll use a 5-column grid with 3 rows: row1 top, row2 middle, row3 bottom
            # col1: QF1 (row1), QF2 (row3)
            # col2: SF1 (row2)
            # col3: Final (row2)
            # col4: SF2 (row2)
            # col5: QF3 (row1), QF4 (row3)
            # We'll put each match in a div with grid-column and grid-row styles

            visual = f'''
            <div class="bracket-wrap">
                <div class="bracket-board" style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr 1fr; grid-template-rows:auto auto auto; gap:20px 8px; min-width:640px; padding:0.5rem; justify-items:center; align-items:center;">
                    <!-- Row 1: QF1 (col1), QF3 (col5) -->
                    <div style="grid-column:1; grid-row:1; width:100%;" class="bracket-arrow">{match_html(left_qf1, 'QF 1')}</div>
                    <div style="grid-column:5; grid-row:1; width:100%;" class="bracket-arrow-left">{match_html(right_qf1, 'QF 3')}</div>
                    <!-- Row 2: SF1 (col2), Final (col3), SF2 (col4) -->
                    <div style="grid-column:2; grid-row:2; width:100%;" class="bracket-arrow">{sf1_html}</div>
                    <div style="grid-column:3; grid-row:2; width:100%;">{final_html}</div>
                    <div style="grid-column:4; grid-row:2; width:100%;" class="bracket-arrow-left">{sf2_html}</div>
                    <!-- Row 3: QF2 (col1), QF4 (col5) -->
                    <div style="grid-column:1; grid-row:3; width:100%;" class="bracket-arrow">{match_html(left_qf2, 'QF 2')}</div>
                    <div style="grid-column:5; grid-row:3; width:100%;" class="bracket-arrow-left">{match_html(right_qf2, 'QF 4')}</div>
                </div>
            </div>
            '''
            st.markdown(visual, unsafe_allow_html=True)

            st.markdown('<div class="knockout-title">Match results</div>', unsafe_allow_html=True)

            def render_tie_editor(tie, title):
                is_qf = title.startswith("QF")
                leg1_no = db.QF_LEG1 if is_qf else db.SF_LEG1
                leg2_no = db.QF_LEG2 if is_qf else db.SF_LEG2
                data = tie_data(tie, leg1_no, leg2_no)
                if not data:
                    return
                f1, f2, a, b, agg, away, winner, reason = data
                round_has_next = db._round_exists(db.list_fixtures(league["id"]), (db.SF_LEG1, db.SF_LEG2)) if is_qf else db._round_exists(db.list_fixtures(league["id"]), (db.FINAL_LEG,))
    
                with st.container(border=True):
                    st.markdown(f"**{title}** — {f1['home_ign']} vs {f1['away_ign']}")
                    for label, f in (("Leg 1", f1), ("Leg 2", f2)):
                        home_label = f"{f['home_ign']} (H)"
                        away_label = f"{f['away_ign']} (A)"
                        if f["played"]:
                            c1, c2 = st.columns([3, 1])
                            c1.markdown(f"**{label}:** {home_label} vs {away_label} — :green[**{f['home_score']} – {f['away_score']}**]")
                            if not round_has_next and league.get("status") == "active":
                                undo_key = f"po_undo_confirm_{f['id']}"
                                if st.session_state.get(undo_key):
                                    c1.caption("Undo this result?")
                                    if c2.button("Yes, undo", key=f"po_undo_yes_{f['id']}", use_container_width=True):
                                        db.unmark_result(f["id"])
                                        st.session_state.pop(undo_key, None)
                                        st.rerun()
                                    if c2.button("Cancel", key=f"po_undo_no_{f['id']}", use_container_width=True):
                                        st.session_state.pop(undo_key, None)
                                        st.rerun()
                                else:
                                    if c2.button("Undo", key=f"po_undo_{f['id']}", use_container_width=True):
                                        st.session_state[undo_key] = True
                                        st.rerun()
                            elif round_has_next:
                                c2.caption("🔒 Round advanced")
                        elif league.get("status") == "active":
                            c1, c2, c3 = st.columns([1, 1, 1.25])
                            hs = c1.number_input(f"{label} {home_label}", min_value=0, max_value=20, step=1, key=f"po_hs_{f['id']}")
                            aws = c2.number_input(f"{label} {away_label}", min_value=0, max_value=20, step=1, key=f"po_as_{f['id']}")
                            if c3.button(f"Save {label}", key=f"po_played_{f['id']}", use_container_width=True):
                                db.submit_result(f["id"], int(hs), int(aws))
                                st.rerun()
                    st.caption(f"Aggregate: {agg[a]} – {agg[b]}  •  Away goals: {away[a]} – {away[b]}")
                    if winner:
                        win_name = f1["home_ign"] if winner == a else f1["away_ign"]
                        st.success(f"{win_name} advances ({reason}).")

            for i, tie in enumerate(qf_groups, 1):
                render_tie_editor(tie, f"QF {i}")
            for i, tie in enumerate(sf_groups, 1):
                render_tie_editor(tie, f"SF {i}")

            if final:
                f = final[0]
                st.markdown('<div class="knockout-title">Final — one match</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown(f'**{f["home_ign"]}** vs **{f["away_ign"]}**')
                    if f["played"]:
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f':green[🏆 **{f["home_score"]} – {f["away_score"]}**]')
                        if league.get("status") == "active":
                            undo_key = f"po_final_undo_confirm_{f['id']}"
                            if st.session_state.get(undo_key):
                                c2.caption("Undo this result?")
                                if c2.button("Yes, undo", key=f"po_final_undo_yes_{f['id']}", use_container_width=True):
                                    db.unmark_result(f["id"])
                                    st.session_state.pop(undo_key, None)
                                    st.rerun()
                                if c2.button("Cancel", key=f"po_final_undo_no_{f['id']}", use_container_width=True):
                                    st.session_state.pop(undo_key, None)
                                    st.rerun()
                            else:
                                if c2.button("Undo", key=f"po_final_undo_{f['id']}", use_container_width=True):
                                    st.session_state[undo_key] = True
                                    st.rerun()
                        champion = db.playoff_champion(league["id"])
                        if champion:
                            winner_name = f["home_ign"] if champion == f["home_player_id"] else f["away_ign"]
                            st.success(f"🏆 Champion: {winner_name}")
                    elif league.get("status") == "active":
                        c1, c2, c3 = st.columns([1, 1, 1.25])
                        hs = c1.number_input("Final H", min_value=0, max_value=20, step=1, key=f"po_final_hs_{f['id']}")
                        aws = c2.number_input("Final A", min_value=0, max_value=20, step=1, key=f"po_final_as_{f['id']}")
                        if c3.button("Save Final", key=f"po_final_{f['id']}", use_container_width=True):
                            db.submit_result(f["id"], int(hs), int(aws))
                            st.rerun()
        else:
            st.info("The top-8 playoff bracket will appear here once the league stage is completed.")


# ------------------------------------------------------------------- History --
elif page_key == "history":
    completed = db.list_completed_leagues()
    if not completed:
        st.markdown('<p class="muted">No completed leagues yet — first champion is still TBD.</p>', unsafe_allow_html=True)
    else:
        for lg in completed:
            winner = lg.get("winner")
            winner_str = f"{winner['ign']} ({winner['club_name']})" if winner else "—"
            with st.expander(f"🏆 {lg['name']} — winner: {winner_str}"):
                table = db.get_standings(lg["id"])
                render_table(standings_rows(table), top8_marker=True)


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
5. **Playoffs** — the top 8 enter quarter-finals, then semi-finals, with Home & Away ties until the single-match final.
6. **Away goals** — if a two-legged tie is level on aggregate, the team with more away goals advances. If away goals are also level, Game will go to penalty shootouts without extratime as the game itslef doesn't have 2 legged ties and tracking the results from previous tie becomes a problem.""")


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
                    st.markdown(f'<p class="muted">{label} deadline: <b>{current.strftime("%d %b %Y")}, 12:00 PM</b> ({status}).</p>', unsafe_allow_html=True)
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
                st.markdown('<p class="muted">🔓 Leg 2 is unlocked.</p>', unsafe_allow_html=True)
            else:
                all_leg1_done = db.leg1_complete(active_league["id"])
                fixtures_now = [f for f in db.list_fixtures(active_league["id"]) if f["leg"] in (1, 2)]
                leg1_total = sum(1 for f in fixtures_now if f["leg"] == 1)
                leg1_played = sum(1 for f in fixtures_now if f["leg"] == 1 and f["played"])
                st.markdown(f'<p class="muted">Leg 1 progress: {leg1_played}/{leg1_total} played</p>', unsafe_allow_html=True)
                if st.button("🔓 Unlock Leg 2 matches", disabled=not all_leg1_done):
                    db.unlock_leg2(active_league["id"])
                    st.rerun()
                if not all_leg1_done:
                    st.markdown('<p class="muted">Unlock becomes available once every Leg 1 fixture is played (including automatic deadline resolutions).</p>', unsafe_allow_html=True)

            league_done = db.league_stage_complete(active_league["id"])
            table_now = db.get_standings(active_league["id"])
            st.markdown('<p class="section-title" style="font-size: 1rem;">Start playoffs</p>', unsafe_allow_html=True)
            if league_done:
                if len(table_now) >= 8:
                    st.markdown('<p class="muted">League stage complete. The top 8 will be seeded into the knockout bracket: 1v8, 4v5, 2v7, 3v6.</p>', unsafe_allow_html=True)
                    if st.button("🏆 Finish league stage & create Top 8 playoffs", type="primary", use_container_width=True):
                        try:
                            db.create_playoffs(active_league["id"])
                            st.success("League stage locked — quarter-finals created.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                else:
                    st.warning(f"League stage is complete, but only {len(table_now)} teams are in the table. Top-8 playoffs need at least 8 teams.")
            else:
                st.markdown('<p class="muted">Finish every league fixture first. Once all matches are done, the Top 8 playoff button will unlock.</p>', unsafe_allow_html=True)

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
                if st.button("➕ Add to league"):
                    try:
                        db.add_player_to_league(active_league["id"], new_player_id)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            st.success("🏆 League stage complete — Top 8 playoffs are in progress. Knockout rounds advance automatically when each tie is finished.")
            po = db.list_fixtures(active_league["id"])
            final = next((f for f in po if f["leg"] == db.FINAL_LEG), None)
            champion = db.playoff_champion(active_league["id"])
            if champion:
                players = {p["id"]: p for p in db.list_players()}
                winner = players.get(champion)
                winner_name = f"{winner['ign']} ({winner['club_name']})" if winner else "Champion"
                st.success(f"🏆 {winner_name} has won the season!")
                if st.button("🏁 Archive season", type="primary", use_container_width=True):
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
                    if st.button("🗑️ Delete this match", key=f"orphan_del_{f['id']}", disabled=not confirm_del):
                        db.delete_fixture(f["id"])
                        st.rerun()

        st.markdown('<p class="muted">Made a mistake starting this one? Cancel it below instead of archiving it — this deletes the league and all its fixtures with no undo.</p>', unsafe_allow_html=True)
        cancel_confirm = st.checkbox("Confirm cancel — delete this league", key="cancel_active_confirm")
        if st.button("🗑️ Cancel & delete this league", disabled=not cancel_confirm):
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

        if st.button("🚀 Start league", type="primary"):
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
            if c3.button("🗑️ Delete", key=f"del_league_{lg['id']}", disabled=not confirm):
                db.delete_league(lg["id"])
                st.rerun()
