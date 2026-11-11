"""
app/components/tab_upload.py
Tab 3 — Upload Âm Thanh & Trích Xuất Librosa Thời Gian Thực
Project: What Makes a Hit Song? (Comparing Chart Performance: VN, US, KR)
Owner: Member 2 (Audio Features & Showcase Engineer)

Luồng:
  1. Upload file âm thanh (.mp3 / .wav / .flac / .ogg)
  2. Kiểm tra kích thước <= 15 MB trước khi xử lý
  3. Trích xuất 17 đặc trưng âm học qua audio_extractor (cached SHA-256)
  4. Hiển thị bảng đặc trưng & các metric nổi bật (đơn vị vật lý chuẩn xác)
  5. Người dùng chọn thị trường -> dự đoán điểm số song hành (Dual-Model: OLS + RF)
     kết hợp Fallback ca từ từ data/processed/lyrics_market_medians.json

Audio Contract v2 (bắt buộc tuân thủ):
  - OLS Model 3: Sử dụng 14 biến âm học liên tục + mode (34 cột design matrix).
  - Nghiêm cấm đưa loudness_proxy và spectral_bandwidth vào OLS (tránh VIF 20.96 và 6.26).
  - Random Forest Model 4: Sử dụng đủ 17 đặc trưng âm học để bắt quan hệ phi tuyến.
  - Fallback ca từ: Nạp trung vị 6 biến ca từ từ lyrics_market_medians.json (TV3 bàn giao).
"""

from __future__ import annotations

import hashlib
import json
import warnings
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

# ── Graceful Streamlit Import (cho phép chạy headless test khi chưa có UI) ──
try:
    import streamlit as st
except ImportError:
    class _MockStreamlitContext:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __getattr__(self, name: str):
            return lambda *args, **kwargs: _MockStreamlitContext()

    class _MockStreamlit:
        session_state: Dict[str, Any] = {}

        @staticmethod
        def cache_data(*args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def columns(self, spec, *args, **kwargs):
            n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
            return [_MockStreamlitContext() for _ in range(n)]

        def expander(self, *args, **kwargs):
            return _MockStreamlitContext()

        def spinner(self, *args, **kwargs):
            return _MockStreamlitContext()

        def selectbox(self, label, options, *args, **kwargs):
            return options[0] if options else None

        def __getattr__(self, name: str):
            return lambda *args, **kwargs: None

    st = _MockStreamlit()  # type: ignore

# ── Root path resolution ────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]

# ── Constants ───────────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB = 15
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_FORMATS = ["mp3", "wav", "flac", "ogg", "m4a"]

MARKET_LABELS = {"VN": "🇻🇳 Việt Nam", "US": "🇺🇸 Hoa Kỳ", "KR": "🇰🇷 Hàn Quốc"}
MARKET_CODES = {"🇻🇳 Việt Nam": "VN", "🇺🇸 Hoa Kỳ": "US", "🇰🇷 Hàn Quốc": "KR"}

# Nhóm 17 đặc trưng để hiển thị
FEATURE_GROUPS: Dict[str, list[str]] = {
    "🥁 Nhịp điệu & Năng lượng": [
        "tempo",
        "onset_rate",
        "tempo_stability",
        "energy",
        "rms_variability",
    ],
    "🎵 Phổ & Hòa âm": [
        "spectral_centroid",
        "spectral_bandwidth",
        "loudness_proxy",
        "chord_change_rate",
        "key_confidence",
        "mode",
    ],
    "🔁 Cấu trúc lặp lại (Chroma & MFCC)": [
        "chroma_repetition_determinism",
        "chroma_mean_pattern_duration",
        "chroma_longest_pattern_duration",
        "mfcc_repetition_determinism",
        "mfcc_mean_pattern_duration",
        "mfcc_longest_pattern_duration",
    ],
}

FEATURE_META: Dict[str, Dict[str, str]] = {
    "tempo":                        {"label": "Tempo",                 "unit": "BPM",        "fmt": ".1f"},
    "onset_rate":                   {"label": "Onset Rate",            "unit": "onsets/min", "fmt": ".1f"},
    "tempo_stability":              {"label": "Độ ổn định nhịp",       "unit": "",           "fmt": ".4f"},
    "energy":                       {"label": "Energy (RMS²)",         "unit": "",           "fmt": ".4f"},
    "rms_variability":              {"label": "RMS Variability",       "unit": "",           "fmt": ".4f"},
    "spectral_centroid":            {"label": "Spectral Centroid",     "unit": "Hz",         "fmt": ".1f"},
    "spectral_bandwidth":           {"label": "Spectral Bandwidth",    "unit": "Hz",         "fmt": ".1f"},
    "loudness_proxy":               {"label": "Loudness Proxy",        "unit": "dBFS",       "fmt": ".2f"},
    "chord_change_rate":            {"label": "Chord Change Rate",     "unit": "chords/min", "fmt": ".1f"},
    "key_confidence":               {"label": "Độ tin cậy giọng điệu", "unit": "",           "fmt": ".4f"},
    "mode":                         {"label": "Mode (Trưởng/Thứ)",     "unit": "",           "fmt": ""},
    "chroma_repetition_determinism":{"label": "Chroma DET",            "unit": "",           "fmt": ".4f"},
    "chroma_mean_pattern_duration": {"label": "Chroma Mean Pattern",   "unit": "s",          "fmt": ".2f"},
    "chroma_longest_pattern_duration":{"label":"Chroma Longest Pattern","unit": "s",         "fmt": ".1f"},
    "mfcc_repetition_determinism":  {"label": "MFCC DET",              "unit": "",           "fmt": ".4f"},
    "mfcc_mean_pattern_duration":   {"label": "MFCC Mean Pattern",     "unit": "s",          "fmt": ".2f"},
    "mfcc_longest_pattern_duration":{"label": "MFCC Longest Pattern",  "unit": "s",          "fmt": ".1f"},
}


# ── Core Helpers ─────────────────────────────────────────────────────────────

def _sha256(data: bytes) -> str:
    """SHA-256 hash của bytes nội dung file — dùng làm cache key chống trùng lặp."""
    return hashlib.sha256(data).hexdigest()


def _inspect_audio_duration(file_bytes: bytes) -> Tuple[Optional[float], Optional[str]]:
    """
    Kiểm tra nhanh thời lượng âm thanh bằng soundfile.info mà không cần giải mã toàn bộ mảng sóng vào RAM.
    Bảo vệ ứng dụng trước các tệp dài bất thường (podcast, DJ mix) vượt quá 360 giây.
    """
    try:
        import soundfile as sf
        info = sf.info(BytesIO(file_bytes))
        return float(info.duration), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


@st.cache_data(show_spinner=False, max_entries=3, ttl=1800)
def _extract_cached(file_sha256: str, _audio_bytes: bytes) -> Tuple[Dict[str, Any], str]:
    """
    Trích xuất 17 đặc trưng âm học (cached theo SHA-256 nội dung file).

    Parameters
    ----------
    file_sha256 : str
        Hash SHA-256 của file — dùng làm cache key (không dùng filename).
    _audio_bytes : bytes
        Nội dung raw của file âm thanh (tiền tố '_' để Streamlit bỏ qua hashing lặp lại).

    Returns
    -------
    (features_dict, error_message)
        error_message rỗng nếu thành công.
    """
    import time
    import tracemalloc
    from src.features.audio_extractor import extract_features_for_inference  # type: ignore

    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    else:
        tracemalloc.reset_peak()

    t0 = time.perf_counter()
    try:
        features = extract_features_for_inference(BytesIO(_audio_bytes))
        t1 = time.perf_counter()
        _, peak_b = tracemalloc.get_traced_memory()

        features["_dsp_latency_sec"] = float(t1 - t0)
        features["_dsp_peak_ram_mb"] = float(peak_b / (1024 * 1024))
        return features, ""
    except ValueError as exc:
        return {}, str(exc)
    except Exception as exc:  # noqa: BLE001
        return {}, f"Lỗi không mong đợi khi trích xuất âm thanh: {exc}"
    finally:
        if not was_tracing and tracemalloc.is_tracing():
            tracemalloc.stop()


@st.cache_data(show_spinner=False)
def _load_lyrics_medians() -> Dict[str, Dict[str, float]]:
    """
    Nạp dữ liệu trung vị ca từ theo 3 thị trường từ data/processed/lyrics_market_medians.json (TV3 bàn giao).
    Trả về dict dạng: {"VN": {...}, "US": {...}, "KR": {...}}.
    """
    path = ROOT_DIR / "data" / "processed" / "lyrics_market_medians.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    result: Dict[str, Dict[str, float]] = {}
    for market, v in raw.get("markets", {}).items():
        result[market] = dict(v.get("medians", {}))
    return result


@st.cache_data(show_spinner=False)
def _load_train_medians() -> Dict[str, float]:
    """Nạp train_medians từ models/feature_metadata.json (dùng làm global fallback cấp 2)."""
    path = ROOT_DIR / "models" / "feature_metadata.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return meta.get("train_medians", {})


def _build_prediction_payload(
    features: Dict[str, Any],
    market: str,
    lyrics_medians: Dict[str, float],
    train_medians: Dict[str, float],
) -> Dict[str, Any]:
    """
    Ghép vector đặc trưng chuẩn bị cho DualModelPredictor:
    - 17 đặc trưng âm học thô từ audio_extractor
    - 6 biến ca từ fallback từ trung vị thị trường (TV3)
    - release_year mặc định 2024
    - market theo lựa chọn người dùng (VN/US/KR)
    """
    lyrics_cols = [
        "word_count", "repetition_ratio", "avg_word_length",
        "line_count", "chorus_repetition_count", "punctuation_ratio",
    ]
    payload = dict(features)
    for col in lyrics_cols:
        val = lyrics_medians.get(col) if lyrics_medians else None
        if val is None:
            val = train_medians.get(col, 0.0)
        payload[col] = float(val)

    payload["market"] = str(market).upper()
    payload["release_year"] = 2024.0
    return payload


def _predict_dual_models(payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, float]], str]:
    """
    Gọi DualModelPredictor từ src.utils.pipeline_inference để dự đoán song hành:
    - OLS Model 3 (tuân thủ Audio Contract v2)
    - Random Forest Model 4 (benchmark phi tuyến)
    - Ensemble Prediction

    Returns
    -------
    (result_dict, error_message)
    """
    try:
        from src.utils.pipeline_inference import get_predictor

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            predictor = get_predictor()

        res = predictor.predict(payload)
        return res, ""
    except Exception as exc:  # noqa: BLE001
        return None, f"Lỗi dự đoán từ pipeline inference: {exc}"


# ── UI Helpers ───────────────────────────────────────────────────────────────

def _fmt_feature_val(key: str, val: Any) -> str:
    """Format giá trị số thuần túy của đặc trưng (không kèm đơn vị)."""
    if key == "mode":
        return "Major 🎵" if float(val) >= 0.5 else "Minor 🎶"
    meta = FEATURE_META.get(key, {})
    fmt = meta.get("fmt", ".4f")
    if fmt:
        try:
            return f"{float(val):{fmt}}"
        except (ValueError, TypeError):
            return str(val)
    return str(val)


def _fmt_feature(key: str, val: Any) -> str:
    """Format giá trị đặc trưng kèm đơn vị chuẩn xác."""
    val_str = _fmt_feature_val(key, val)
    if key == "mode":
        return val_str
    unit = FEATURE_META.get(key, {}).get("unit", "")
    return f"{val_str} {unit}".strip()


def _render_feature_table(features: Dict[str, Any]) -> None:
    """Hiển thị 17 đặc trưng theo 3 nhóm cấu trúc âm học."""
    for group_name, keys in FEATURE_GROUPS.items():
        with st.expander(group_name, expanded=True):
            rows = []
            for k in keys:
                meta = FEATURE_META.get(k, {})
                val = features.get(k)
                if val is None:
                    continue
                rows.append({
                    "Đặc trưng": meta.get("label", k),
                    "Giá trị": _fmt_feature_val(k, val),
                    "Đơn vị": meta.get("unit", ""),
                })
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)


def _render_highlight_metrics(features: Dict[str, Any]) -> None:
    """Hiển thị 4 metric tiêu điểm hàng đầu."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎵 Tempo", f"{features.get('tempo', 0):.1f} BPM")
    col2.metric("⚡ Energy (RMS²)", f"{features.get('energy', 0):.4f}")
    col3.metric("📡 Spectral Centroid", f"{features.get('spectral_centroid', 0):.0f} Hz")
    key_root = features.get("key", "")
    mode_name = "Major 🎵" if float(features.get("mode", 1)) >= 0.5 else "Minor 🎶"
    full_key = f"{key_root} {mode_name}".strip() if key_root else mode_name
    col4.metric("🎹 Điệu tính & Giọng", full_key)


def _render_prediction_result(
    pred: Dict[str, float],
    market_label: str,
    market_code: str = "VN",
) -> None:
    """
    Hiển thị kết quả dự đoán điểm số song hành và đối chuẩn mẫu hình âm học theo thị trường.
    Sử dụng get_acoustic_fit_profile từ src.utils.tier_classifier để quy chiếu phân vị
    thay vì áp đặt các ngưỡng điểm thô gây lỗi co cụm trung vị (Shrinkage to Mean).
    """
    from src.utils.tier_classifier import get_acoustic_fit_profile

    ols_score = pred.get("ols_prediction", 0.0)
    rf_score = pred.get("rf_prediction", 0.0)
    ensemble = pred.get("ensemble_prediction", 0.0)

    # Đối chuẩn bách phân vị âm học theo thị trường bằng Random Forest
    profile = get_acoustic_fit_profile(rf_score, market=market_code, model_type="rf")

    st.subheader(f"🎯 Kết Quả Dự Đoán Song Hành & Đối Chuẩn Âm Học ({market_label})")

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "📈 Hồi quy Tuyến tính OLS (Model 3)",
        f"{ols_score:.1f} điểm",
        help="Mô hình chuẩn kinh tế lượng: giải thích ảnh hưởng biên và tương tác thị trường (Thang điểm chuẩn hóa [-99, +100]).",
    )
    c2.metric(
        "🌲 Rừng Ngẫu Nhiên (Model 4 RF)",
        f"{rf_score:.1f} điểm",
        help="Mô hình phi tuyến phi tham số: đo lường cấu trúc tương tác phi tuyến tính (Thang điểm chuẩn hóa [-99, +100]).",
    )
    c3.metric(
        "⚖️ Điểm Tổ Hợp (Ensemble)",
        f"{ensemble:.1f} điểm",
        help="Điểm bình quân trọng số 50-50 giữa OLS và Random Forest (Thang điểm chuẩn hóa [-99, +100]).",
    )

    st.markdown("---")
    st.markdown(
        f"#### {profile['badge_color']} Vị Trí Mẫu Hình Âm Học: **Top {profile['top_percent']:.0f}%** "
        f"Thị Trường {market_label} — *{profile['tier_title']}*"
    )
    st.progress(min(1.0, max(0.0, profile["percentile"] / 100.0)))

    if profile["is_top22"]:
        st.success(
            f"🏆 **XÁC THỰC ÂM HỌC: LỌT NHÓM MẪU HÌNH DẪN ĐẦU (TOP 22% THỊ TRƯỜNG {market_label.upper()})**\n\n"
            f"- **Vị thế Âm học:** Cấu trúc âm thanh của ca khúc tiệm cận nhóm 22% điểm dự đoán cao nhất tại thị trường {market_label} "
            f"(Vị trí tương đối: **Top {profile['top_percent']:.0f}%**).\n"
            f"- **Kiểm chứng độc lập (n=410 bài test):** Nhóm ca khúc thuộc phân tầng này có **xác suất đạt Hit thực tế lên đến 44.1%** "
            f"(gấp 1.76 lần mức ngẫu nhiên 25.1%, Fisher Exact $p < 0.0001$, Odds Ratio = 3.24), với điểm BXH thực tế trung bình cao hơn **+13.3 đến +17.8 điểm** ($p < 0.01$).\n"
            f"- *Khuyến cáo:* Âm học là bệ phóng vững chắc (điều kiện cần); thành công thương mại vẫn cần bệ phóng truyền thông và độ nhận diện nghệ sĩ (MAE ≈ 30 điểm)."
        )
    elif profile["tier_code"] == "Tier 2":
        st.warning(
            f"⭐ **MẪU HÌNH ÂM HỌC CHUẨN ĐẠI CHÚNG (TOP {profile['top_percent']:.0f}% THỊ TRƯỜNG {market_label.upper()})**\n\n"
            f"- {profile['description']}\n"
            f"- **Khuyến nghị sản xuất:** Cấu trúc bài hát đạt độ hài hòa tốt với thị hiếu người nghe đại chúng. Để bứt phá thành Mega-hit, ca khúc cần sự hỗ trợ mạnh mẽ từ chiến dịch marketing và vị trí playlisting nổi bật."
        )
    elif profile["tier_code"] == "Tier 3":
        st.info(
            f"📈 **MẪU HÌNH ÂM HỌC THỂ NGHIỆM / PHÂN HÓA (TOP {profile['top_percent']:.0f}% THỊ TRƯỜNG {market_label.upper()})**\n\n"
            f"- {profile['description']}\n"
            f"- **Khuyến nghị sản xuất:** Cấu trúc âm nhạc mang nét cá tính riêng biệt hoặc kén người nghe đại chúng. Thích hợp hướng tới phân khúc khán giả ngách hoặc cộng đồng người nghe trung thành."
        )
    else:
        st.error(
            f"📉 **MẪU HÌNH ÂM HỌC LỆCH CHUẨN THỊ TRƯỜNG (TOP {profile['top_percent']:.0f}% THỊ TRƯỜNG {market_label.upper()})**\n\n"
            f"- {profile['description']}\n"
            f"- **Khuyến nghị sản xuất:** Ca khúc lệch xa khỏi các chuẩn mực âm học thường thấy trên BXH {market_label}. Cân nhắc rà soát lại các chỉ số năng lượng (Energy), độ lớn (Loudness proxy) hoặc nhịp độ (Tempo) nếu mục tiêu là tiếp cận đại chúng."
        )

    st.caption(
        "📌 **Lưu ý phương pháp luận & Cơ sở học thuật:**\n"
        "- **Tái định vị Phân tầng Âm học ([Herremans et al., 2019](https://arxiv.org/pdf/1905.08076)):** "
        "Do các đặc trưng âm thanh thuần túy chỉ giải thích từ 3.4% – 6.9% biến thiên thành tích thương mại ($R^2_{\\text{OOS}}$), "
        "điểm dự đoán có xu hướng co cụm về trung vị (*Shrinkage to Mean*). Việc phân tầng được tính dựa trên **bách phân vị nội bộ từng thị trường** "
        "từ dữ liệu đóng băng, giúp đánh giá vị thế tiệm cận mẫu hình âm học một cách khách quan.\n"
        "- **Bản chất Văn liệu Hit Song Science ([Salganik et al., 2006](https://pdodds.w3.uvm.edu/research/papers/years/2006/salganik2006a.pdf); "
        "[Pachet & Roy, 2008](https://csl.sony.fr/wp-content/uploads/2008/01/pachet-08c.pdf)):** "
        "Thành công âm nhạc chịu chi phối áp đảo bởi ảnh hưởng xã hội và chiến lược tiếp thị ([Jiang, 2024](https://www.scitepress.org/PublishedPapers/2024/133300); "
        "[Nijkamp, 2018](https://essay.utwente.nl/essays/75422)). Đặc trưng âm thanh là điều kiện cần nhưng không đủ để đảm bảo thứ hạng đơn lẻ (MAE ≈ 29–30 điểm).\n"
        "- **Thiên lệch chọn mẫu (Range Restriction):** Bộ dữ liệu chỉ gồm bài hát đã lọt vào Spotify Top 200/Top 50 (đã qua vòng tuyển trạch tự nhiên), "
        "dẫn đến dải phương sai bị cắt cụt, kéo $R^2$ xuống thấp hơn so với khi kiểm nghiệm trên toàn bộ kho nhạc đại trà.\n"
        "- **Fallback Ca từ:** Tệp âm thanh tải lên chưa có lời được nạp trung vị 6 biến ca từ của "
        f"{market_label} từ `lyrics_market_medians.json` (tập Train n=1,685 do TV3 bàn giao)."
    )


# ── Main render function ──────────────────────────────────────────────────────

def render() -> None:
    """
    Giao diện chính Tab 3 — Upload Âm Thanh & Trích Xuất Librosa Thời Gian Thực.
    Được import và gọi từ app/main.py.
    """
    st.header("🎙️ Tải Lên Âm Thanh & Trích Xuất Librosa Thời Gian Thực")
    st.caption(
        "Trích xuất trực tiếp 17 đặc trưng âm thanh số (DSP) bằng Librosa và dự đoán thành tích "
        "bằng kiến trúc mô hình song hành (OLS Model 3 & Random Forest Model 4)."
    )

    left_col, right_col = st.columns([1, 2], gap="large")

    with left_col:
        st.subheader("📂 Chọn file âm thanh")
        uploaded = st.file_uploader(
            label="Kéo thả hoặc chọn file nhạc",
            type=SUPPORTED_FORMATS,
            help=f"Hỗ trợ: {', '.join(f'.{e}' for e in SUPPORTED_FORMATS)} | Dung lượng tối đa {MAX_FILE_SIZE_MB} MB",
            key="tab3_uploader",
        )

        st.subheader("🌏 Thị trường đánh giá")
        market_label = st.selectbox(
            "Chọn thị trường mục tiêu",
            options=list(MARKET_CODES.keys()),
            key="tab3_market_select",
            help="Thị trường quyết định vector dummy, hệ số độ dốc tương tác và bộ trung vị ca từ.",
        )
        market_code = MARKET_CODES.get(market_label, "VN")

        with st.expander("ℹ️ Tiêu chuẩn Kỹ thuật Phân hệ", expanded=False):
            st.markdown(
                f"""
                - **Giới hạn an toàn:** Tối đa {MAX_FILE_SIZE_MB} MB, giải mã tối đa 360 giây (6 phút).
                - **Librosa DSP Engine:** Trích xuất 17 đặc trưng âm thanh số (DSP) thời gian thực, tự động giải phóng bộ đệm sau xử lý.
                - **Audio Contract v2:** OLS chỉ dùng 14 biến liên tục + mode (cấm `loudness_proxy` và `spectral_bandwidth`).
                - **Fallback Ca từ:** Đồng bộ trung vị thị trường từ `lyrics_market_medians.json` (TV3).
                - **Hiệu năng:** Caching `@st.cache_data` qua mã băm SHA-256 nội dung file.
                """
            )

    with right_col:
        if uploaded is None:
            st.session_state.pop("tab3_predictions", None)
            st.session_state.pop("tab3_current_file_sha", None)
            st.info("⬅️ Hãy kéo thả hoặc chọn một tệp âm thanh ở cột bên trái để bắt đầu phân tích.")
            return

        file_bytes = uploaded.getvalue()
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            st.error(
                f"❌ File vượt quá giới hạn an toàn {MAX_FILE_SIZE_MB} MB "
                f"(dung lượng tệp: {file_size_mb:.1f} MB). "
                "Vui lòng cắt ngắn hoặc nén tệp trước khi tải lên."
            )
            return

        # Pre-check thời lượng âm thanh bằng metadata header trước khi decode Librosa
        est_duration, _ = _inspect_audio_duration(file_bytes)
        if est_duration is not None:
            if est_duration > 360.0:
                st.warning(
                    f"⏱️ **Lưu ý thời lượng:** Tệp gốc có thời lượng {est_duration:.1f} giây (> 6 phút). "
                    "Hệ thống sẽ chuẩn hóa và giải mã 360 giây đầu tiên (6 phút) theo tiêu chuẩn bảo vệ tài nguyên."
                )
            elif est_duration < 10.0:
                st.warning(
                    f"⚠️ **Cảnh báo thời lượng:** Tệp ngắn ({est_duration:.1f}s < 10s). "
                    "Các chỉ số phân tích cấu trúc lặp (Chroma & MFCC RQA) có thể trở về 0 do không đủ độ dài lặp."
                )

        st.success(f"✅ Đã nạp tệp thành công: **{uploaded.name}** ({file_size_mb:.2f} MB)")
        audio_ext = uploaded.name.split(".")[-1].lower() if "." in uploaded.name else "mp3"
        audio_mime = "audio/mp4" if audio_ext == "m4a" else f"audio/{audio_ext}"
        st.audio(file_bytes, format=audio_mime)

        file_sha = _sha256(file_bytes)
        cache_key = f"tab3_features_{file_sha}"

        if cache_key not in st.session_state:
            with st.spinner("🔬 Đang phân tích tín hiệu âm thanh Librosa... (Lần đầu có thể mất 15–20s do Numba JIT compile)"):
                features, err = _extract_cached(file_sha, file_bytes)
            st.session_state[cache_key] = (features, err)
        else:
            features, err = st.session_state[cache_key]

        if err:
            if "im lặng" in err.lower() or "silent" in err.lower():
                st.warning(f"⚠️ Phát hiện âm thanh bất thường (quá im lặng):\n\n{err}")
            elif "15mb" in err.lower() or "size" in err.lower():
                st.error(f"❌ {err}")
            else:
                st.error(f"❌ Không thể phân tích tệp âm thanh:\n\n{err}")
            return

        if not features:
            st.error("❌ Quá trình trích xuất không trả về kết quả.")
            return

        duration = features.get("duration_analyzed_seconds", 0)
        key_name = features.get("key", "N/A")
        if est_duration is not None and est_duration > 360.0:
            duration_desc = f"**{duration:.1f} giây** (trích đoạn 6 phút đầu từ tệp gốc {est_duration:.1f}s)"
        else:
            duration_desc = f"**{duration:.1f} giây**"

        lat = features.get("_dsp_latency_sec", 0.0)
        ram = features.get("_dsp_peak_ram_mb", 0.0)
        telemetry = f" | ⚡ Độ trễ DSP: **{lat:.2f}s** | 💾 RAM đỉnh DSP (tracemalloc): **~{ram:.1f} MB**" if lat > 0 else ""

        st.caption(
            f"⏱️ Thời lượng giải mã: {duration_desc} | "
            f"🎼 Điệu tính ước lượng: **{key_name}** {'Major 🎵' if float(features.get('mode', 1)) >= 0.5 else 'Minor 🎶'}"
            f"{telemetry}"
        )

        st.subheader("📊 Tiêu Điểm Âm Học")
        _render_highlight_metrics(features)

        st.subheader("📋 Bảng Thông Số 17 Đặc Trưng Âm Học (Librosa DSP)")
        _render_feature_table(features)

        st.markdown("---")

        st.subheader(f"🎯 Dự Đoán Thành Tích Tại Thị Trường {market_label}")
        st.info(
            f"ℹ️ **Cơ chế Fallback Ca từ:** Tệp âm thanh tải lên chưa có lời. "
            f"Hệ thống sẽ nạp trung vị 6 đặc trưng ca từ của **{market_label}** từ `lyrics_market_medians.json` "
            "để tạo vector đầu vào hoàn chỉnh cho mô hình."
        )

        # Đồng bộ hóa bộ nhớ đệm dự đoán theo tệp và thị trường
        if "tab3_predictions" not in st.session_state:
            st.session_state["tab3_predictions"] = {}

        # Làm mới kết quả nếu người dùng thay đổi tệp âm thanh
        if st.session_state.get("tab3_current_file_sha") != file_sha:
            st.session_state["tab3_current_file_sha"] = file_sha
            st.session_state["tab3_predictions"] = {}

        pred_key = f"{file_sha}_{market_code}"

        predict_btn = st.button(
            f"🔮 Chạy Mô Hình Dự Đoán Song Hành ({market_label})",
            key="tab3_predict_btn",
            type="primary",
        )

        if predict_btn:
            lyrics_medians_all = _load_lyrics_medians()
            train_medians = _load_train_medians()
            market_medians = lyrics_medians_all.get(market_code, {})

            if not market_medians:
                st.warning(
                    f"⚠️ Không tìm thấy bảng trung vị riêng cho thị trường {market_code}. "
                    "Hệ thống tự động sử dụng trung vị chung toàn tập huấn luyện."
                )

            payload = _build_prediction_payload(features, market_code, market_medians, train_medians)

            with st.spinner("⚙️ Đang tính toán qua OLS Model 3 & Random Forest Model 4..."):
                pred_res, pred_err = _predict_dual_models(payload)

            if pred_err:
                st.error(pred_err)
            elif pred_res is not None:
                st.session_state["tab3_predictions"][pred_key] = pred_res

        # Hiển thị kết quả tương ứng chính xác với thị trường hiện tại
        if pred_key in st.session_state["tab3_predictions"]:
            current_pred = st.session_state["tab3_predictions"][pred_key]
            _render_prediction_result(current_pred, market_label, market_code=market_code)
        else:
            st.info(f"💡 Nhấn nút trên để tính toán dự đoán điểm số tại **{market_label}**.")


# Alias to conform with team-wide naming conventions (e.g. render_tab_diagnostics)
render_tab_upload = render
