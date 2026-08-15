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
    winner_player_id uuid references players(id),
    started_at timestamptz not null default now(),
    completed_at timestamptz
);

-- Which players are in a given league
create table if not exists league_participants (
    league_id uuid not null references leagues(id) on delete cascade,
    player_id uuid not null references players(id),
    primary key (league_id, player_id)
);

-- Fixtures (auto-generated home & away round robin when a league starts)
create table if not exists fixtures (
    id uuid primary key default gen_random_uuid(),
    league_id uuid not null references leagues(id) on delete cascade,
    home_player_id uuid not null references players(id),
    away_player_id uuid not null references players(id),
    leg int not null check (leg in (1, 2)), -- 1 = first meeting, 2 = reverse fixture
    played boolean not null default false,
    home_score int,
    away_score int,
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
