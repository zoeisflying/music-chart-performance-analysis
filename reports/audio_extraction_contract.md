# Audio Extraction Contract

## 1. Purpose

This document defines the audio feature extraction conventions used in the Music Chart Performance Analysis project.

It documents four duplicate feature pairs identified in `src/audio/build_audio_features_master.py`. Each legacy feature is directly assigned from its corresponding canonical feature.

To avoid redundant variables and perfect multicollinearity in downstream modeling, the project retains canonical features and excludes their duplicate aliases.

## 2. Duplicate Audio Feature Pairs

### Pair 1: Tempo

**Canonical feature:** `tempo_bpm`  
**Duplicate alias:** `tempo`

Source code:

```python
master["tempo"] = master["tempo_bpm"]
```

Mathematical relationship:

\[
tempo = tempo\_bpm
\]

`tempo_bpm` is obtained from Librosa's beat tracking:

```python
tempo, beat_times = librosa.beat.beat_track(
    y=y,
    sr=sr,
    hop_length=HOP_LENGTH,
    units="time",
)
tempo_bpm = scalar(tempo)
```

The alias `tempo` is an exact copy of `tempo_bpm`, not an independently extracted feature.

### Pair 2: RMS Energy

**Canonical feature:** `rms_energy`  
**Duplicate alias:** `energy`

Source code:

```python
master["energy"] = master["rms_energy"]
```

Mathematical relationship:

\[
energy = rms\_energy
\]

The RMS value for each audio frame is:

\[
RMS_j = \sqrt{\frac{1}{L}\sum_{n=1}^{L}x_j[n]^2}
\]

The final `rms_energy` feature is the mean RMS across all valid frames:

\[
rms\_energy = \frac{1}{M}\sum_{j=1}^{M}RMS_j
\]

Where:

- \(L\): Number of audio samples in each frame.
- \(M\): Number of valid RMS frames.
- \(x_j[n]\): Audio amplitude at sample \(n\) of frame \(j\).

Invalid RMS values are excluded before calculating the mean.

### Pair 3: Dynamic Range

**Canonical feature:** `dynamic_range`  
**Duplicate alias:** `loudness_proxy`

Source code:

```python
master["loudness_proxy"] = master["dynamic_range"]
```

Mathematical relationship:

\[
loudness\_proxy = dynamic\_range
\]

The dynamic range is calculated from the frame-level RMS values after excluding invalid values.

First, RMS values are converted to decibels relative to full scale (dBFS):

\[
RMS_{dBFS,j}=20\log_{10}(\max(RMS_j,\epsilon))
\]

The 90th and 10th percentiles are then calculated:

\[
P_{90}=\operatorname{Percentile}(RMS_{dBFS},90)
\]

\[
P_{10}=\operatorname{Percentile}(RMS_{dBFS},10)
\]

The final dynamic range is:

\[
dynamic\_range=P_{90}-P_{10}
\]

Where:

- \(RMS_j\): RMS amplitude of frame \(j\).
- \(\epsilon\): `RMS_EPSILON`, a small positive value used to prevent taking the logarithm of zero.
- \(P_{90}\): 90th percentile of frame-level RMS values in dBFS.
- \(P_{10}\): 10th percentile of frame-level RMS values in dBFS.

The legacy alias `loudness_proxy` is an exact copy of `dynamic_range`, not an independently extracted feature.

### Pair 4: Beat Interval Variability

**Canonical feature:** `beat_interval_variability`  
**Duplicate alias:** `tempo_stability`

Source code:

```python
master["tempo_stability"] = master["beat_interval_variability"]
```

Mathematical relationship:

\[
tempo\_stability = beat\_interval\_variability
\]

Beat times are detected using Librosa. The time intervals between consecutive beats are calculated as:

\[
\Delta_i = t_{i+1}-t_i
\]

The feature is calculated as the population standard deviation of beat intervals:

\[
beat\_interval\_variability =
\sqrt{\frac{1}{n}\sum_{i=1}^{n}(\Delta_i-\bar{\Delta})^2}
\]

Where:

- \(t_i\): Timestamp of beat \(i\).
- \(\Delta_i\): Time interval between consecutive beats.
- \(\bar{\Delta}\): Mean beat interval.
- \(n\): Number of calculated beat intervals.

The implementation uses `np.std(beat_intervals, ddof=0)`. If fewer than three beat timestamps are available, the feature is assigned `NaN`.

## 3. Correlation and Modeling Implications

For every duplicate pair, the legacy feature is assigned directly from the canonical feature.

Therefore, their values are identical for each record. Provided the feature has non-zero variance, their Pearson correlation is:

\[
r(X,Y)=1.0
\]

Keeping both columns would introduce redundant information and perfect multicollinearity into regression models.

The project therefore retains one canonical feature from each pair.

## 4. Canonical Feature Selection

| Canonical feature (Keep) | Legacy alias (Exclude) |
|---|---|
| `tempo_bpm` | `tempo` |
| `rms_energy` | `energy` |
| `dynamic_range` | `loudness_proxy` |
| `beat_interval_variability` | `tempo_stability` |

## 5. Downstream Data Contract

All downstream modeling datasets should:

1. Use canonical feature names.
2. Exclude the four duplicate legacy aliases.
3. Preserve the original canonical feature values.
4. Avoid independently recalculating legacy aliases.
5. Apply consistent feature definitions across all markets.

The clean modeling dataset follows this convention by retaining the four canonical features and excluding their duplicate aliases.

## 6. Source Code References

- `src/audio/extract_rhythm.py`: Beat tracking and beat interval variability calculation.
- `src/audio/extract_energy.py`: Frame-level RMS calculation and aggregation.
- `src/audio/build_audio_features_master.py`: Legacy alias assignments and master dataset construction.
