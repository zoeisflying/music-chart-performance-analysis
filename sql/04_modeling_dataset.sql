-- =============================================================================
-- sql/04_modeling_dataset.sql
-- Owner: Member 4 (Data Integration, Quality Control & Master Reports)
-- Grain: 1 row = 1 (spotify_track_id, market)
-- Purpose: Integrates Chart Target, Song Metadata, Audio Features, and Lyrics Features.
-- Safe to re-run: Idempotent DROP and CREATE VIEW.
-- =============================================================================

BEGIN;

DROP VIEW IF EXISTS public.modeling_dataset CASCADE;

CREATE VIEW public.modeling_dataset AS
SELECT
    -- 1. Primary Identification & Market
    cp.spotify_track_id,
    cp.market,

    -- 2. Target Variable & Descriptive Chart Metrics (Member 1)
    cp.lifetime_average_rank,
    cp.chart_score,
    cp.peak_rank,
    cp.weeks_on_chart,
    cp.weeks_in_top10,

    -- 3. Song Metadata (Songs table)
    s.title,
    s.artist,
    s.album,
    s.release_date,
    EXTRACT(YEAR FROM s.release_date)::INTEGER AS release_year,

    -- 4. Acoustic Features (Member 2 - 20 Signal Dimensions)
    af.tempo_bpm,
    af.onset_rate,
    af.beat_interval_variability,
    af.tempo_stability,
    af.rms_energy,
    af.rms_variability,
    af.dynamic_range,
    af.loudness_proxy,
    af.spectral_centroid,
    af.spectral_bandwidth,
    af.duration_seconds,
    af.duration_analyzed_seconds,
    af.key AS audio_key,
    af.mode AS audio_mode,
    af.key_confidence,
    af.chord_change_rate,
    af.chroma_repetition_determinism,
    af.chroma_mean_pattern_duration,
    af.chroma_longest_pattern_duration,
    af.mfcc_repetition_determinism,
    af.mfcc_mean_pattern_duration,
    af.mfcc_longest_pattern_duration,

    -- 5. Audio Video Mapping Verification
    af.youtube_mapping_id,
    ym.is_selected AS audio_mapping_is_selected,

    -- 6. Linguistic & NLP Features (Member 3 - 10 Text Dimensions)
    lf.word_count,
    lf.unique_word_count,
    lf.lexical_diversity,
    lf.repetition_ratio,
    lf.avg_word_length,
    lf.line_count,
    lf.chorus_repetition_count,
    lf.title_word_in_lyrics,
    lf.punctuation_ratio,
    lf.pronoun_ratio,
    lf.language AS lyrics_language,
    lf.lyrics_status,

    -- 7. Audit & Completeness Flags
    (af.spotify_track_id IS NOT NULL) AS has_audio,
    (lf.spotify_track_id IS NOT NULL AND lf.lyrics_status = 'success') AS has_lyrics,
    (
        af.spotify_track_id IS NOT NULL
        AND lf.spotify_track_id IS NOT NULL
        AND lf.lyrics_status = 'success'
    ) AS is_complete_case,
    (
        EXISTS (
            SELECT 1
            FROM public.song_quarter_sampling q
            WHERE q.spotify_track_id = cp.spotify_track_id
        )
    ) AS is_sampled

FROM public.chart_performance cp
JOIN public.songs s
    ON s.spotify_track_id = cp.spotify_track_id
LEFT JOIN public.audio_features af
    ON af.spotify_track_id = cp.spotify_track_id
LEFT JOIN public.youtube_mapping ym
    ON ym.id = af.youtube_mapping_id
LEFT JOIN public.lyrics_features lf
    ON lf.spotify_track_id = cp.spotify_track_id;

COMMENT ON VIEW public.modeling_dataset IS 
    'Unified modeling dataset joining songs, chart_performance, audio_features, and lyrics_features at (spotify_track_id, market) grain.';

COMMIT;
