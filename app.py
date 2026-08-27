import streamlit as st
import db
from datetime import date

st.set_page_config(page_title="PES With the Bois", page_icon="🟣", layout="wide", initial_sidebar_state="collapsed")

PAGE_LABELS = {
    "home": "Home",
    "fixtures": "Fixtures",
    "table": "League Standing",
    "history": "History",
    "register": "Register",
    "rules": "Rules",
    "admin": "Admin",
}

PAGE_ICONS = {
    "fixtures": "⚽",
    "table": "🏆",
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

@media (max-width: 640px) {
    .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
    .brand-bar { font-size: 1.25rem; }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div { font-size: 1.4rem; }

    table.league-table { min-width: 0; width: 100%; font-size: 0.66rem; }
    table.league-table th, table.league-table td { padding: 4px 5px; }
    .club-sub { font-size: 0.78em; }

    /* fixture cards: give inputs/buttons a bit more breathing room */
    div[data-testid="stNumberInput"] input { padding: 6px 8px; font-size: 0.9rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] { padding: 0.6rem !important; }
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


def render_table(rows: list[dict]):
    """Renders a list of dicts as the sketch-style bordered table."""
    if not rows:
        st.markdown('<p class="muted">No results yet.</p>', unsafe_allow_html=True)
        return
    cols = list(rows[0].keys())
    html = ['<div class="league-table-wrap"><table class="league-table"><thead><tr>']
    for c in cols:
        html.append(f"<th>{c}</th>")
    html.append("</tr></thead><tbody>")
    for r in rows:
        html.append("<tr>")
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

st.markdown('<div class="brand-bar">PES With the Bois</div>', unsafe_allow_html=True)


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
    raw = league.get("deadline") if leg == 1 else league.get("leg2_deadline")
    return bool(raw) and date.today() > date.fromisoformat(raw)


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

    tile_rows = [["fixtures", "table"], ["history", "register"], ["rules", "admin"]]
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
        fixtures = db.list_fixtures(league["id"])

        leg1_closed = leg_deadline_passed(league, 1)
        leg2_closed = leg_deadline_passed(league, 2)

        raw_deadline = league.get("deadline")
        if raw_deadline:
            deadline_date = date.fromisoformat(raw_deadline)
            if leg1_closed:
                st.markdown(
                    f'<p class="muted">⏰ Leg 1 deadline was <b>{deadline_date.strftime("%d %b %Y")}</b> — '
                    f'Leg 1 is now closed.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<p class="muted">⏳ Leg 1 deadline: <b>{deadline_date.strftime("%d %b %Y")}</b></p>', unsafe_allow_html=True)

        raw_leg2_deadline = league.get("leg2_deadline")
        if raw_leg2_deadline:
            leg2_deadline_date = date.fromisoformat(raw_leg2_deadline)
            if leg2_closed:
                st.markdown(
                    f'<p class="muted">⏰ Leg 2 deadline was <b>{leg2_deadline_date.strftime("%d %b %Y")}</b> — '
                    f'Leg 2 is now closed.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<p class="muted">⏳ Leg 2 deadline: <b>{leg2_deadline_date.strftime("%d %b %Y")}</b></p>', unsafe_allow_html=True)

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
        render_table(standings_rows(table))


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
                render_table(standings_rows(table))


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
4. **In-game rules** — keep Extra Time and Penalties turned OFF.
""")


# --------------------------------------------------------------------- Admin --
elif page_key == "admin":
    pw = st.text_input("Admin password", type="password")
    if pw != st.secrets.get("ADMIN_PASSWORD", ""):
        st.warning("Enter the admin password to continue.")
        st.stop()

    st.success("Logged in as admin.")

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
        if c4.button("Remove", key=f"rm_{p['id']}"):
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
    active_league = db.get_active_league()

    if active_league:
        st.write(f"Active league: **{active_league['name']}**")

        st.markdown('<p class="section-title" style="font-size: 1rem;">Leg 1 deadline</p>', unsafe_allow_html=True)
        raw_deadline = active_league.get("deadline")
        current_deadline_date = date.fromisoformat(raw_deadline) if raw_deadline else None
        deadline_passed = current_deadline_date is not None and date.today() > current_deadline_date

        if current_deadline_date:
            if deadline_passed:
                st.markdown(
                    f'<p class="muted">⏰ Deadline was <b>{current_deadline_date.strftime("%d %b %Y")}</b> — passed. '
                    f'Overdue Leg 1 fixtures can be forfeited below.</p>', unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<p class="muted">Deadline: <b>{current_deadline_date.strftime("%d %b %Y")}</b></p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="muted">No Leg 1 deadline set — forfeits for Leg 1 are off until you set one.</p>', unsafe_allow_html=True)

        new_deadline = st.date_input("Set / change Leg 1 deadline", value=current_deadline_date or date.today(), key="deadline_input")
        dc1, dc2 = st.columns(2)
        if dc1.button("Update Leg 1 deadline", use_container_width=True):
            db.set_league_deadline(active_league["id"], new_deadline)
            st.success("Leg 1 deadline updated.")
            st.rerun()
        if dc2.button("Clear Leg 1 deadline", use_container_width=True, disabled=not current_deadline_date):
            db.set_league_deadline(active_league["id"], None)
            st.success("Leg 1 deadline cleared.")
            st.rerun()

        st.markdown('<p class="section-title" style="font-size: 1rem;">Leg 2 deadline</p>', unsafe_allow_html=True)
        raw_leg2_deadline = active_league.get("leg2_deadline")
        current_leg2_deadline_date = date.fromisoformat(raw_leg2_deadline) if raw_leg2_deadline else None
        leg2_deadline_passed = current_leg2_deadline_date is not None and date.today() > current_leg2_deadline_date

        if not active_league["leg2_unlocked"]:
            st.markdown('<p class="muted">Leg 2 is still locked — you can set a deadline now, but it only makes sense once Leg 2 opens up.</p>', unsafe_allow_html=True)

        if current_leg2_deadline_date:
            if leg2_deadline_passed:
                st.markdown(
                    f'<p class="muted">⏰ Deadline was <b>{current_leg2_deadline_date.strftime("%d %b %Y")}</b> — passed. '
                    f'Overdue Leg 2 fixtures can be forfeited below.</p>', unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<p class="muted">Deadline: <b>{current_leg2_deadline_date.strftime("%d %b %Y")}</b></p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="muted">No Leg 2 deadline set — forfeits for Leg 2 are off until you set one.</p>', unsafe_allow_html=True)

        new_leg2_deadline = st.date_input("Set / change Leg 2 deadline", value=current_leg2_deadline_date or date.today(), key="leg2_deadline_admin_input")
        lc1, lc2 = st.columns(2)
        if lc1.button("Update Leg 2 deadline", use_container_width=True):
            db.set_league_leg2_deadline(active_league["id"], new_leg2_deadline)
            st.success("Leg 2 deadline updated.")
            st.rerun()
        if lc2.button("Clear Leg 2 deadline", use_container_width=True, disabled=not current_leg2_deadline_date):
            db.set_league_leg2_deadline(active_league["id"], None)
            st.success("Leg 2 deadline cleared.")
            st.rerun()

        st.markdown('<p class="section-title" style="font-size: 1rem;">Leg 2 lock</p>', unsafe_allow_html=True)
        if active_league["leg2_unlocked"]:
            st.markdown('<p class="muted">🔓 Leg 2 is unlocked — reverse fixtures can be played.</p>', unsafe_allow_html=True)
        else:
            all_leg1_done = db.leg1_complete(active_league["id"])
            fixtures_now = db.list_fixtures(active_league["id"])
            leg1_total = sum(1 for f in fixtures_now if f["leg"] == 1)
            leg1_played = sum(1 for f in fixtures_now if f["leg"] == 1 and f["played"])
            st.markdown(f'<p class="muted">Leg 1 progress: {leg1_played}/{leg1_total} played</p>', unsafe_allow_html=True)
            if st.button("🔓 Unlock Leg 2 matches", disabled=not all_leg1_done):
                db.unlock_leg2(active_league["id"])
                st.success("Leg 2 unlocked — reverse fixtures can now be played.")
                st.rerun()
            if not all_leg1_done:
                st.markdown('<p class="muted">Unlocks automatically becomes available once every Leg 1 fixture is played.</p>', unsafe_allow_html=True)

        if st.button("🏁 Complete this league (locks table, tags winner)", type="primary"):
            try:
                db.complete_league(active_league["id"])
                st.success("League completed and archived.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.markdown('<p class="section-title" style="font-size: 1rem;">Add a player mid-season</p>', unsafe_allow_html=True)
        st.markdown('<p class="muted">Slots them in with fresh home & away fixtures against everyone already in the league. Your existing results are untouched.</p>', unsafe_allow_html=True)
        existing_ids = db.get_league_participant_ids(active_league["id"])
        approved_active = [p for p in db.list_players(status="approved") if p["active"]]
        joinable = [p for p in approved_active if p["id"] not in existing_ids]
        if not joinable:
            st.markdown('<p class="muted">No approved players left to add — everyone approved is already in this league.</p>', unsafe_allow_html=True)
        else:
            new_player_id = st.selectbox(
                "Player to add", options=[p["id"] for p in joinable],
                format_func=lambda pid: player_label(next(p for p in joinable if p["id"] == pid)),
            )
            if st.button("➕ Add to league"):
                try:
                    db.add_player_to_league(active_league["id"], new_player_id)
                    st.success("Added — fixtures generated against the rest of the league.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        st.markdown('<p class="section-title" style="font-size: 1rem;">Forfeits</p>', unsafe_allow_html=True)
        st.markdown('<p class="muted">Overdue matches now get auto-resolved (fewer matches played in that leg = the forfeit loss, equal counts = a 1-1 draw) the moment anyone loads the app after the deadline. This section is just a manual fallback / rarely needed.</p>', unsafe_allow_html=True)
        if not deadline_passed and not leg2_deadline_passed:
            st.markdown('<p class="muted">No deadline has passed yet — nothing to forfeit.</p>', unsafe_allow_html=True)
        else:
            all_fixtures = db.list_fixtures(active_league["id"])
            overdue = [
                f for f in all_fixtures if not f["played"] and (
                    (f["leg"] == 1 and deadline_passed) or (f["leg"] == 2 and leg2_deadline_passed)
                )
            ]
            if not overdue:
                st.markdown('<p class="muted">No overdue unplayed fixtures right now.</p>', unsafe_allow_html=True)
            else:
                for f in overdue:
                    with st.expander(f"⏰ {f['home_ign']} vs {f['away_ign']}  (Leg {f['leg']})"):
                        outcome_choice = st.radio(
                            "Outcome",
                            options=["home", "draw", "away"],
                            format_func=lambda w, f=f: (
                                f"{f['home_ign']} ({f['home_club_name']}) wins 1-0" if w == "home"
                                else "Draw 1-1 — no forfeit loser" if w == "draw"
                                else f"{f['away_ign']} ({f['away_club_name']}) wins 1-0"
                            ),
                            key=f"forfeit_choice_{f['id']}",
                        )
                        if st.button("Apply result", key=f"forfeit_apply_{f['id']}"):
                            db.apply_forfeit(f["id"], outcome_choice)
                            st.success("Forfeit result applied.")
                            st.rerun()

        st.markdown('<p class="section-title" style="font-size: 1rem;">Matches involving removed players</p>', unsafe_allow_html=True)
        st.markdown('<p class="muted">When you remove a player, any match they already played is kept as real history — but it leaves their opponent with one extra match compared to everyone else. If that\'s throwing off comparisons, you can wipe that specific match here.</p>', unsafe_allow_html=True)
        orphaned = db.get_orphaned_fixtures(active_league["id"])
        if not orphaned:
            st.markdown('<p class="muted">None right now.</p>', unsafe_allow_html=True)
        else:
            for f in orphaned:
                score = f"{f['home_score']}-{f['away_score']}" if f["played"] else "unplayed"
                with st.expander(f"{f['home_ign']} vs {f['away_ign']} (Leg {f['leg']}) — {score}"):
                    st.markdown('<p class="muted">One of these players has since been removed. Deleting this match removes it from the standings entirely (both sides), bringing match counts back in line.</p>', unsafe_allow_html=True)
                    confirm_del = st.checkbox("Confirm delete — no undo", key=f"confirm_orphan_del_{f['id']}")
                    if st.button("🗑️ Delete this match", key=f"orphan_del_{f['id']}", disabled=not confirm_del):
                        db.delete_fixture(f["id"])
                        st.success("Match deleted.")
                        st.rerun()

        st.markdown('<p class="section-title" style="font-size: 1rem;">Closed-leg fixtures (admin edit)</p>', unsafe_allow_html=True)
        st.markdown('<p class="muted">Once a leg\'s deadline passes, players can no longer tick or undo results for it — only you can correct a score from here (e.g. an auto-resolved forfeit that should\'ve been a real result).</p>', unsafe_allow_html=True)
        closed_legs = [leg for leg, passed in ((1, deadline_passed), (2, leg2_deadline_passed)) if passed]
        if not closed_legs:
            st.markdown('<p class="muted">No leg is closed yet.</p>', unsafe_allow_html=True)
        else:
            closed_fixtures = [f for f in db.list_fixtures(active_league["id"]) if f["leg"] in closed_legs]
            for f in closed_fixtures:
                tag = " · 🚩 forfeit" if f.get("forfeit") else ""
                score = f"{f['home_score']}-{f['away_score']}" if f["played"] else "unplayed"
                with st.expander(f"{f['home_ign']} vs {f['away_ign']} (Leg {f['leg']}){tag} — {score}"):
                    ec1, ec2, ec3 = st.columns([1, 1, 1.4])
                    new_hs = ec1.number_input("Home", min_value=0, max_value=20, value=f["home_score"] or 0, key=f"edit_hs_{f['id']}")
                    new_aws = ec2.number_input("Away", min_value=0, max_value=20, value=f["away_score"] or 0, key=f"edit_as_{f['id']}")
                    ec3.markdown("<div style='height: 1.6rem'></div>", unsafe_allow_html=True)
                    if ec3.button("Save correction", key=f"edit_save_{f['id']}", use_container_width=True):
                        db.submit_result(f["id"], int(new_hs), int(new_aws))
                        st.success("Result corrected.")
                        st.rerun()
                    if f["played"] and st.button("Revert to unplayed", key=f"edit_revert_{f['id']}"):
                        db.unmark_result(f["id"])
                        st.success("Reverted — fixture is unplayed again.")
                        st.rerun()

        st.markdown('<p class="muted">Made a mistake starting this one (wrong players, test league, etc)? Cancel it below instead of completing it — this deletes it with no archive.</p>', unsafe_allow_html=True)
        cancel_confirm = st.checkbox("Confirm cancel — this deletes the league and its fixtures, no undo", key="cancel_active_confirm")
        if st.button("🗑️ Cancel & delete this league", disabled=not cancel_confirm):
            db.delete_league(active_league["id"])
            st.success("League cancelled and deleted.")
            st.rerun()
    else:
        st.write("No active league. Start one from approved, active players:")
        approved = [p for p in db.list_players(status="approved") if p["active"]]
        chosen = st.multiselect(
            "Select participants", options=[p["id"] for p in approved],
            format_func=lambda pid: player_label(next(p for p in approved if p["id"] == pid)),
        )
        league_name = st.text_input("League name", value="Season 1")

        set_deadline = st.checkbox("Set a Leg 1 deadline (missed matches can be forfeited)")
        deadline_val = None
        if set_deadline:
            deadline_val = st.date_input("Leg 1 deadline date", min_value=date.today(), key="leg1_deadline_input")

        set_leg2_deadline = st.checkbox("Set a Leg 2 deadline too")
        leg2_deadline_val = None
        if set_leg2_deadline:
            leg2_min = deadline_val if deadline_val else date.today()
            leg2_deadline_val = st.date_input("Leg 2 deadline date", min_value=leg2_min, key="leg2_deadline_input")
            st.markdown('<p class="muted">You can always set or adjust this later once Leg 2 actually unlocks.</p>', unsafe_allow_html=True)

        if st.button("🚀 Start league", type="primary"):
            if len(chosen) < 2:
                st.error("Pick at least 2 players.")
            else:
                try:
                    db.start_new_league(league_name, chosen, deadline=deadline_val, leg2_deadline=leg2_deadline_val)
                    st.success("League started — fixtures generated.")
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
                st.success(f"Deleted {lg['name']}.")
                st.rerun()
