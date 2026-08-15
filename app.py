import streamlit as st
import db

st.set_page_config(page_title="eFootball GC League", page_icon="⚽", layout="wide")

PAGES = ["Join / Register", "Fixtures", "Table", "History", "Admin"]


def player_label(p):
    return f"{p['ign']}  ({p['club_name']})"


# --------------------------------------------------------------------- UI --

st.title("⚽ eFootball Mobile — GC League")

page = st.sidebar.radio("Go to", PAGES)


# ---------------------------------------------------------- Join/Register --
if page == "Join / Register":
    st.header("Join the league")
    st.write("Enter your club name and in-game name. The admin will approve you before you show up in fixtures.")

    with st.form("register_form", clear_on_submit=True):
        club_name = st.text_input("Club name")
        ign = st.text_input("In-game name (IGN)")
        submitted = st.form_submit_button("Submit for approval")
        if submitted:
            if not club_name or not ign:
                st.error("Both fields are required.")
            else:
                try:
                    db.register_player(club_name, ign)
                    st.success("Submitted! Waiting on admin approval.")
                except Exception as e:
                    st.error(str(e))

    st.divider()
    st.subheader("Approved players")
    approved = db.list_players(status="approved")
    if approved:
        st.dataframe(
            [{"Club": p["club_name"], "IGN": p["ign"], "Active": p["active"]} for p in approved],
            use_container_width=True, hide_index=True,
        )
    else:
        st.caption("No approved players yet.")


# ------------------------------------------------------------- Fixtures ---
elif page == "Fixtures":
    st.header("Fixtures")
    league = db.get_active_league()

    if not league:
        st.info("No active league right now. An admin needs to start one.")
    else:
        st.subheader(league["name"])
        fixtures = db.list_fixtures(league["id"])
        players = {p["id"]: p for p in db.list_players()}

        approved_players = [p for p in db.list_players(status="approved") if p["active"]]
        names = {p["id"]: player_label(p) for p in approved_players}
        me = st.selectbox(
            "I am...", options=[None] + list(names.keys()),
            format_func=lambda pid: "— select your name —" if pid is None else names[pid],
        )

        if me:
            nxt = db.next_fixture_for_player(league["id"], me)
            if nxt:
                st.success(
                    f"Your next fixture: **{player_label(nxt['home'])}** vs "
                    f"**{player_label(nxt['away'])}**  (leg {nxt['leg']})"
                )
            else:
                st.info("You have no unplayed fixtures left — nice, you're done for this cycle.")

        st.divider()
        st.subheader("Full fixture list")
        st.caption("Tick a fixture once it's been played and enter the score. Ticked fixtures turn green.")

        for f in fixtures:
            home, away = f["home"], f["away"]
            cols = st.columns([4, 1, 1, 1, 1])
            label = f"{player_label(home)}  vs  {player_label(away)}  (leg {f['leg']})"

            if f["played"]:
                cols[0].markdown(f":green[✅ {label}]  —  **{f['home_score']} – {f['away_score']}**")
                if cols[4].button("Undo", key=f"undo_{f['id']}"):
                    db.unmark_result(f["id"])
                    st.rerun()
            else:
                cols[0].markdown(label)
                hs = cols[1].number_input("H", min_value=0, max_value=20, step=1, key=f"hs_{f['id']}", label_visibility="collapsed")
                aws = cols[2].number_input("A", min_value=0, max_value=20, step=1, key=f"as_{f['id']}", label_visibility="collapsed")
                if cols[3].button("✅ Tick", key=f"tick_{f['id']}"):
                    db.submit_result(f["id"], int(hs), int(aws))
                    st.rerun()


# ---------------------------------------------------------------- Table ---
elif page == "Table":
    st.header("League Table")
    league = db.get_active_league()

    if not league:
        st.info("No active league right now.")
    else:
        st.subheader(league["name"])
        table = db.get_standings(league["id"])
        if not table:
            st.caption("No results played yet.")
        else:
            rows = [{
                "#": i + 1,
                "Club": r["club_name"], "IGN": r["ign"],
                "P": r["played"], "W": r["won"], "D": r["drawn"], "L": r["lost"],
                "GF": r["gf"], "GA": r["ga"], "GD": r["gd"], "Pts": r["points"],
            } for i, r in enumerate(table)]
            st.dataframe(rows, use_container_width=True, hide_index=True)


# -------------------------------------------------------------- History ---
elif page == "History":
    st.header("League History")
    completed = db.list_completed_leagues()
    if not completed:
        st.caption("No completed leagues yet — first champion is still TBD.")
    else:
        for lg in completed:
            winner = lg.get("winner")
            winner_str = f"{winner['ign']} ({winner['club_name']})" if winner else "—"
            with st.expander(f"🏆 {lg['name']} — winner: {winner_str}"):
                table = db.get_standings(lg["id"])
                rows = [{
                    "#": i + 1, "Club": r["club_name"], "IGN": r["ign"],
                    "P": r["played"], "W": r["won"], "D": r["drawn"], "L": r["lost"],
                    "GF": r["gf"], "GA": r["ga"], "GD": r["gd"], "Pts": r["points"],
                } for i, r in enumerate(table)]
                st.dataframe(rows, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------- Admin ---
elif page == "Admin":
    st.header("Admin")
    pw = st.text_input("Admin password", type="password")
    if pw != st.secrets.get("ADMIN_PASSWORD", ""):
        st.warning("Enter the admin password to continue.")
        st.stop()

    st.success("Logged in as admin.")

    st.subheader("Pending approvals")
    pending = db.list_players(status="pending")
    if not pending:
        st.caption("Nothing pending.")
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

    st.divider()
    st.subheader(f"All players ({db.player_count()}/{db.MAX_PLAYERS} approved)")
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

    st.divider()
    st.subheader("Add a player directly")
    with st.form("admin_add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        club = c1.text_input("Club name")
        ign = c2.text_input("IGN")
        if st.form_submit_button("Add"):
            try:
                db.admin_add_player(club, ign)
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.divider()
    st.subheader("League management")
    active_league = db.get_active_league()

    if active_league:
        st.write(f"Active league: **{active_league['name']}**")
        table = db.get_standings(active_league["id"])
        if st.button("🏁 Complete this league (locks table, tags winner)"):
            try:
                db.complete_league(active_league["id"])
                st.success("League completed and archived.")
                st.rerun()
            except Exception as e:
                st.error(str(e))
    else:
        st.write("No active league. Start one from approved, active players:")
        approved = [p for p in db.list_players(status="approved") if p["active"]]
        chosen = st.multiselect(
            "Select participants", options=[p["id"] for p in approved],
            format_func=lambda pid: player_label(next(p for p in approved if p["id"] == pid)),
        )
        league_name = st.text_input("League name", value="Season 1")
        if st.button("🚀 Start league"):
            if len(chosen) < 2:
                st.error("Pick at least 2 players.")
            else:
                try:
                    db.start_new_league(league_name, chosen)
                    st.success("League started — fixtures generated.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
