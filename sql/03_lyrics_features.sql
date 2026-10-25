-- 03_lyrics_features.sql
-- Owner: Member 3 (Report 3)
-- Grain: 1 row = 1 spotify_track_id (Track-level grain)
-- Re-runnable: idempotent create and upsert

CREATE TABLE IF NOT EXISTS public.lyrics_features (
    spotify_track_id        TEXT PRIMARY KEY REFERENCES public.songs(spotify_track_id) ON DELETE CASCADE,
    word_count              INTEGER,
    unique_word_count       INTEGER,
    lexical_diversity       DOUBLE PRECISION,
    repetition_ratio        DOUBLE PRECISION,
    avg_word_length         DOUBLE PRECISION,
    line_count              INTEGER,
    chorus_repetition_count DOUBLE PRECISION,
    title_word_in_lyrics    BOOLEAN,
    punctuation_ratio       DOUBLE PRECISION,
    pronoun_ratio           DOUBLE PRECISION,
    language                TEXT,
    lyrics_status           TEXT NOT NULL DEFAULT 'pending' CHECK (lyrics_status IN ('pending', 'success', 'not_found', 'failed', 'rejected')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lyrics_features_status ON public.lyrics_features(lyrics_status);
CREATE INDEX IF NOT EXISTS idx_lyrics_features_language ON public.lyrics_features(language);

COMMENT ON TABLE public.lyrics_features IS 'Linguistic and NLP features extracted from cleaned song lyrics.';
COMMENT ON COLUMN public.lyrics_features.word_count IS 'Total recognized word tokens in cleaned lyrics.';
COMMENT ON COLUMN public.lyrics_features.unique_word_count IS 'Count of distinct normalized word tokens.';
COMMENT ON COLUMN public.lyrics_features.lexical_diversity IS 'Type-token ratio: unique_word_count / word_count. Undefined (NULL) if word_count = 0.';
COMMENT ON COLUMN public.lyrics_features.repetition_ratio IS 'Repetition fraction: 1.0 - lexical_diversity.';
COMMENT ON COLUMN public.lyrics_features.avg_word_length IS 'Mean character count per word token.';
COMMENT ON COLUMN public.lyrics_features.line_count IS 'Number of non-empty lyric lines.';
COMMENT ON COLUMN public.lyrics_features.chorus_repetition_count IS 'Number of times detected chorus is repeated; NULL if not identifiable.';
COMMENT ON COLUMN public.lyrics_features.title_word_in_lyrics IS 'True if at least one content title word appears in lyrics.';
COMMENT ON COLUMN public.lyrics_features.punctuation_ratio IS 'Punctuation characters divided by total characters.';
COMMENT ON COLUMN public.lyrics_features.pronoun_ratio IS 'Pronoun tokens divided by word_count using language dictionaries.';
COMMENT ON COLUMN public.lyrics_features.lyrics_status IS 'Processing status: success, not_found, failed, etc.';
