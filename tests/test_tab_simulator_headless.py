"""
tests/test_tab_simulator_headless.py
Headless test suite for Tab 2: What-if Simulator
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from app.components.tab_simulator import render


def test_tab_simulator_render_headless_default():
    """Verify Tab 2 render executes cleanly with default inputs under mock Streamlit."""
    mock_st = MagicMock()

    # Mock form
    mock_form = MagicMock()
    mock_form.__enter__.return_value = mock_form
    mock_form.__exit__.return_value = None
    mock_st.form.return_value = mock_form

    # Mock columns
    col_mocks = []
    def dummy_columns(spec):
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        cols = [MagicMock() for _ in range(n)]
        col_mocks.extend(cols)
        return cols

    mock_st.columns.side_effect = dummy_columns
    mock_st.selectbox.side_effect = lambda label, options, **kwargs: options[0]
    mock_st.slider.side_effect = lambda label, min_val, max_val, val, *args, **kwargs: val
    mock_st.form_submit_button.return_value = False

    with patch.dict(sys.modules, {"streamlit": mock_st}):
        render()

    assert mock_st.header.called
    assert any(col.metric.called for col in col_mocks)
    assert mock_st.progress.called


def test_tab_simulator_render_headless_submitted():
    """Verify Tab 2 render executes with submitted inputs and renders acoustic profile."""
    mock_st = MagicMock()

    mock_form = MagicMock()
    mock_form.__enter__.return_value = mock_form
    mock_form.__exit__.return_value = None
    mock_st.form.return_value = mock_form

    col_mocks = []
    def dummy_columns(spec):
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        cols = [MagicMock() for _ in range(n)]
        col_mocks.extend(cols)
        return cols

    mock_st.columns.side_effect = dummy_columns
    mock_st.selectbox.side_effect = lambda label, options, **kwargs: "VN"
    mock_st.slider.side_effect = lambda label, min_val, max_val, val, *args, **kwargs: val
    mock_st.form_submit_button.return_value = True

    with patch.dict(sys.modules, {"streamlit": mock_st}):
        render()

    assert mock_st.header.called
    assert any(col.metric.called for col in col_mocks)
    assert mock_st.progress.called
