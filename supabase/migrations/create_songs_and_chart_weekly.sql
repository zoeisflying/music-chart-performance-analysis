-- Migration: create_songs_and_chart_weekly
-- Owner: Member 1
-- Description: Bảng songs và chart_weekly chuẩn hóa theo spotify_track_id

create table if not exists songs (
    spotify_track_id text primary key,
    title text not null,
    artist text not null,
    album text,
    release_date date,
    created_at timestamptz default now()
);

create table if not exists chart_weekly (
    id bigint generated always as identity primary key,
    spotify_track_id text not null references songs(spotify_track_id) on delete cascade,
    market text not null check (market in ('VN', 'US', 'KR')),
    chart_date date not null,
    rank int not null check (rank > 0),
    streams bigint,
    constraint uq_chart_weekly unique (spotify_track_id, market, chart_date)
);

create index if not exists idx_chart_weekly_track on chart_weekly (spotify_track_id);
create index if not exists idx_chart_weekly_market_date on chart_weekly (market, chart_date);
create index if not exists idx_chart_weekly_market_rank on chart_weekly (market, rank);

-- Tắt RLS để cho phép nạp dữ liệu từ script bằng anon/publishable key
alter table songs disable row level security;
alter table chart_weekly disable row level security;

