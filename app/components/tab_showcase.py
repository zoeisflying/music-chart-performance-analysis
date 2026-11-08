"""
app/components/tab_showcase.py
Tab 1: Showcase 15 Test Tracks & Acoustic Radar Chart
Owner: Member 4 (Data Integration, Benchmark & Deploy Lead) & Member 2
Data Source: Reads directly from repository files (data/processed/modeling_dataset_clean_cache.csv, models/test_track_ids.json, reports/report4/chart_data/member2/fig5_radar_market_fingerprints.csv)
"""

import json
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.utils.pipeline_inference import get_predictor

ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_PATH = ROOT_DIR / "data" / "processed" / "modeling_dataset_clean_cache.csv"
TEST_IDS_PATH = ROOT_DIR / "models" / "test_track_ids.json"
RADAR_CSV = ROOT_DIR / "reports" / "report4" / "chart_data" / "member2" / "fig5_radar_market_fingerprints.csv"


@st.cache_data
def load_showcase_test_tracks() -> pd.DataFrame:
    """Loads 15 representative tracks from the frozen test set across VN, US, KR."""
    if not CACHE_PATH.exists() or not TEST_IDS_PATH.exists():
        # Fallback dummy if files are not present
        return pd.DataFrame([
            {"title": "See Tình", "artist": "Hoàng Thùy Linh", "market": "VN", "chart_score": 88.5, "tempo": 120.0, "energy": 0.23, "loudness_proxy": -12.5, "onset_rate": 185.0, "spectral_centroid": 2150.0, "chord_change_rate": 42.0},
            {"title": "Anti-Hero", "artist": "Taylor Swift", "market": "US", "chart_score": 94.2, "tempo": 97.0, "energy": 0.24, "loudness_proxy": -10.8, "onset_rate": 195.0, "spectral_centroid": 2240.0, "chord_change_rate": 44.0},
            {"title": "Super Shy", "artist": "NewJeans", "market": "KR", "chart_score": 92.0, "tempo": 150.0, "energy": 0.28, "loudness_proxy": -8.5, "onset_rate": 205.0, "spectral_centroid": 2520.0, "chord_change_rate": 46.0},
        ])

    with open(TEST_IDS_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
    test_ids = set(meta["track_ids"] if isinstance(meta, dict) else meta)

    df = pd.read_csv(CACHE_PATH)
    test_df = df[df["spotify_track_id"].isin(test_ids)].copy()

    # Pick 5 unique tracks per market (total 15)
    selected_list = []
    for mkt in ["VN", "US", "KR"]:
        mkt_sub = test_df[test_df["market"] == mkt].drop_duplicates(subset=["spotify_track_id"])
        # Sort by chart_score descending to pick prominent tracks across tiers
        top_mkt = mkt_sub.sort_values(by="chart_score", ascending=False).head(5)
        selected_list.append(top_mkt)

    res_df = pd.concat(selected_list).reset_index(drop=True)
    return res_df


def render_tab_showcase():
    st.header("🎵 Thư Viện Bài Hát Tiêu Biểu & Radar Chart Âm Học")
    st.markdown(
        """
        Khám phá 15 bài hát đại diện được trích xuất từ tập kiểm thử độc lập (*Held-out Test Set*, $N=410$). 
        Đối chiếu trực quan giữa **Điểm số thực tế** trên Spotify Top 200 với **Dự đoán từ Mô hình OLS (Model 3) và Random Forest (Model 4)**.
        """
    )

    tracks_sample = load_showcase_test_tracks()

    track_options = [
        f"{row['title']} — {row['artist']} ({row['market']})"
        for _, row in tracks_sample.iterrows()
    ]
    selected_option = st.selectbox("Chọn bài hát trong tập kiểm thử (Test Set):", track_options)

    selected_idx = track_options.index(selected_option)
    selected_row = tracks_sample.iloc[selected_idx].to_dict()

    predictor = get_predictor()
    pred_res = predictor.predict(selected_row)

    # 3 Score Comparison Columns
    col1, col2, col3 = st.columns(3)
    actual_score = float(selected_row.get("chart_score", 50.0))
    ols_pred = float(pred_res["ols_prediction"])
    rf_pred = float(pred_res["rf_prediction"])

    col1.metric("🏆 Điểm Thực Tế (Actual)", f"{actual_score:.1f} pts")
    col2.metric("📈 Dự Đoán OLS (Model 3)", f"{ols_pred:.1f} pts", delta=f"{ols_pred - actual_score:+.1f}")
    col3.metric("🌲 Dự Đoán RF (Model 4)", f"{rf_pred:.1f} pts", delta=f"{rf_pred - actual_score:+.1f}")

    # Radar Chart
    st.markdown("---")
    st.subheader("Biểu đồ Mạng Nhện Đặc Trưng Âm Học (Acoustic Radar Chart)")

    categories = ['Tempo', 'Energy (RMS)', 'Loudness', 'Onset Rate', 'Spectral Centroid', 'Chord Change Rate']
    
    # Normalized [0, 1] for radar chart against empirical domain bounds
    norm_values = [
        float(np.clip((selected_row.get("tempo", 120.0) - 60.0) / 140.0, 0.05, 1.0)),
        float(np.clip(selected_row.get("energy", 0.24) / 0.50, 0.05, 1.0)),
        float(np.clip((selected_row.get("loudness_proxy", -12.0) + 25.0) / 20.0, 0.05, 1.0)),
        float(np.clip((selected_row.get("onset_rate", 190.0) - 80.0) / 180.0, 0.05, 1.0)),
        float(np.clip((selected_row.get("spectral_centroid", 2200.0) - 1000.0) / 2800.0, 0.05, 1.0)),
        float(np.clip((selected_row.get("chord_change_rate", 42.0) - 10.0) / 60.0, 0.05, 1.0)),
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=norm_values + [norm_values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(43, 92, 143, 0.35)',
        line=dict(color='#1E3A8A', width=2),
        name=f"{selected_row.get('title', 'Bài hát')} ({selected_row.get('market', '')})"
    ))

    # Optional: Overlay market fingerprint benchmark if fig5_radar CSV exists
    if RADAR_CSV.exists():
        try:
            radar_mkt_df = pd.read_csv(RADAR_CSV)
            m_row = radar_mkt_df[radar_mkt_df["market"] == selected_row.get("market")].iloc[0]
            mkt_vals = [
                float(m_row.get("tempo_bpm", 0.35)),
                float(m_row.get("rms_energy", 0.40)),
                float(m_row.get("rms_energy", 0.40)), # proxy
                float(m_row.get("onset_rate", 0.52)),
                float(m_row.get("spectral_centroid", 0.55)),
                float(m_row.get("chord_change_rate", 0.43)),
            ]
            fig.add_trace(go.Scatterpolar(
                r=mkt_vals + [mkt_vals[0]],
                theta=categories + [categories[0]],
                fill=None,
                line=dict(color='#EF4444', width=1.5, dash='dot'),
                name=f"Trung bình Thị trường {selected_row.get('market')}"
            ))
        except Exception:
            pass

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1.0]),
        ),
        showlegend=True,
        height=480,
        margin=dict(l=40, r=40, t=30, b=30)
    )
    st.plotly_chart(fig, use_container_width=True)
