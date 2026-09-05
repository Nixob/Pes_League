-- eFootball Mobile GC League — Supabase schema
-- Run this whole file once in the Supabase SQL editor.

create extension if not exists "pgcrypto";

-- Players (persist across leagues)
create table if not exists players (
    id uuid primary key default gen_random_uuid(),
    club_name text not null,
    ign text not null,
    active boolean not null default true,
    -- pending players show up when someone self-registers; admin must approve
    -- before they can be added into a league's fixtures.
    status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
    created_at timestamptz not null default now()
);

-- Leagues ("seasons")
create table if not exists leagues (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    status text not null default 'active' check (status in ('active', 'completed')),
    winner_player_id uuid references players(id) on delete set null,
    started_at timestamptz not null default now(),
    completed_at timestamptz,
    -- Leg 1 / Leg 2 close automatically at 12:00 PM IST on these dates
    -- (enforced in app code, not the DB); NULL means "no deadline set".
    deadline date,
    leg2_deadline date,
    -- Leg 2 fixtures are hidden/locked until the admin explicitly opens
    -- them (normally once every Leg 1 fixture has been played).
    leg2_unlocked boolean not null default false
);

-- Which players are in a given league
create table if not exists league_participants (
    league_id uuid not null references leagues(id) on delete cascade,
    player_id uuid not null references players(id) on delete cascade,
    primary key (league_id, player_id)
);

-- Fixtures (auto-generated home & away round robin when a league starts).
-- Also doubles as the knockout-playoff table: leg 1/2 are the league's
-- two legs, and legs 3-7 are the top-8 bracket (3/4 = QF leg1/leg2,
-- 5/6 = SF leg1/leg2, 7 = the single-match final). See QF_LEG1 etc. in
-- db.py for the authoritative mapping.
-- home/away club_name + ign are snapshotted at fixture-creation time so
-- that deleting a player later doesn't erase history.
create table if not exists fixtures (
    id uuid primary key default gen_random_uuid(),
    league_id uuid not null references leagues(id) on delete cascade,
    home_player_id uuid references players(id) on delete set null,
    away_player_id uuid references players(id) on delete set null,
    home_club_name text,
    home_ign text,
    away_club_name text,
    away_ign text,
    leg int not null check (leg between 1 and 7),
    played boolean not null default false,
    home_score int,
    away_score int,
    -- True when this result was auto-resolved (or admin-recorded) as a
    -- no-show rather than an actually-played match.
    forfeit boolean not null default false,
    played_at timestamptz
);

create index if not exists idx_fixtures_league on fixtures(league_id);
create index if not exists idx_fixtures_players on fixtures(home_player_id, away_player_id);

-- Row Level Security: keep it simple for a friends GC (open read/write via anon key).
-- Tighten this later if you ever want real auth.
alter table players enable row level security;
alter table leagues enable row level security;
alter table league_participants enable row level security;
alter table fixtures enable row level security;

create policy "public read players" on players for select using (true);
create policy "public write players" on players for all using (true) with check (true);

create policy "public read leagues" on leagues for select using (true);
create policy "public write leagues" on leagues for all using (true) with check (true);

create policy "public read participants" on league_participants for select using (true);
create policy "public write participants" on league_participants for all using (true) with check (true);

create policy "public read fixtures" on fixtures for select using (true);
create policy "public write fixtures" on fixtures for all using (true) with check (true);
