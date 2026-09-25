-- Migration: 20260922_create_youtube_mapping
-- Owner: Member 2 (YouTube Matching & Raw Audio)
-- Description: Bảng youtube_mapping (Evidence-Based Matching, grain: song x YouTube candidate)
--              và bảng downstream audio_features (grain: 1 song)

create table if not exists youtube_mapping (
    id bigint generated always as identity primary key,
    spotify_track_id text not null references songs(spotify_track_id) on delete cascade,
    candidate_number int check (candidate_number between 1 and 5),
    is_selected boolean not null default false,
    youtube_video_id text,
    youtube_title text,
    youtube_channel text,
    spotify_duration_ms int,
    youtube_duration numeric(10, 2),

    -- 4 nhóm bằng chứng độc lập (Evidence-Based Matching)
    title_similarity numeric(5, 2),
    title_conflict boolean default false,
    version_conflict boolean default false,
    identity_evidence jsonb default '[]'::jsonb,
    source_evidence jsonb default '[]'::jsonb,
    duration_difference_ratio numeric(10, 6),
    hard_invalid boolean default false,

    -- Kết quả phân loại & trạng thái thu thập
    match_method text not null default 'youtube_search',
    is_official boolean default false,
    decision_status text check (
        decision_status in (
            'automatic',
            'ambiguous',
            'no_confident_match',
            'manual_selected'
        )
    ),
    status text not null default 'pending' check (
        status in (
            'pending',
            'processing',
            'success',
            'failed',
            'rejected',
            'not_found'
        )
    ),
    created_at timestamptz default now(),

    constraint uq_youtube_mapping_track_candidate
        unique (spotify_track_id, candidate_number)
);

-- Đảm bảo mỗi bài hát chỉ có tối đa 1 candidate được đánh dấu is_selected = true
create unique index if not exists uq_youtube_mapping_one_selected_per_song
    on youtube_mapping (spotify_track_id)
    where is_selected = true;

create index if not exists idx_youtube_mapping_track
    on youtube_mapping (spotify_track_id);

create index if not exists idx_youtube_mapping_status
    on youtube_mapping (status);

create index if not exists idx_youtube_mapping_decision_status
    on youtube_mapping (decision_status);

-- View tiện ích lấy 1 dòng đại diện duy nhất cho mỗi bài hát (phục vụ tích hợp Member 4)
create or replace view youtube_selected_mapping as
select *
from youtube_mapping
where is_selected = true;

-- Bảng downstream audio_features (Owner: Member 2, Grain: 1 song)
create table if not exists audio_features (
    spotify_track_id text primary key references songs(spotify_track_id) on delete cascade,
    youtube_mapping_id bigint references youtube_mapping(id) on delete set null,
    tempo numeric(10, 4),
    energy numeric(10, 6),
    onset_rate numeric(10, 6),
    loudness_proxy numeric(10, 6),
    tempo_stability numeric(10, 6),
    spectral_centroid numeric(12, 4),
    spectral_bandwidth numeric(12, 4),
    key int,
    mode int,
    created_at timestamptz default now()
);

-- Tắt RLS để cho phép nạp dữ liệu từ script bằng anon/publishable key (đồng bộ với Member 1)
alter table youtube_mapping disable row level security;
alter table audio_features disable row level security;