# -*- coding: utf-8 -*-
# Tests unitarios para output.py

import sys, os, json, csv, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from output import (
    ensure_output_dir, export_group_stage_csv, export_group_stage_json,
    export_group_tables_csv, export_knockout_csv, export_knockout_json,
    export_full_prode_csv, export_all, OUTPUT_DIR,
)


@pytest.fixture
def tmp_dir():
    old = OUTPUT_DIR
    td = tempfile.mkdtemp()
    import output
    output.OUTPUT_DIR = td
    yield td
    output.OUTPUT_DIR = old


def _dummy_prediction(team_a="Argentina", team_b="Brazil", venue="Miami",
                       score_a=2, score_b=1, prob_a=45.0, prob_d=30.0, prob_b=25.0,
                       round_name="Group A", conf=50.0, xg_a=1.8, xg_b=1.2):
    return {
        "team_a": team_a, "team_b": team_b, "venue": venue,
        "venue_country": "USA",
        "score_a": score_a, "score_b": score_b,
        "prob_a_win": prob_a, "prob_draw": prob_d, "prob_b_win": prob_b,
        "round": round_name, "confidence": conf,
        "expected_goals_a": xg_a, "expected_goals_b": xg_b,
        "winner": team_a, "loser": team_b,
        "factors": {"team_strength": 0.5, "morale": 0.0},
    }


def _dummy_group_results():
    return {"A": [("Team1", {"pts": 6, "w": 2, "d": 0, "l": 1, "gf": 5, "ga": 2, "gd": 3}),
                   ("Team2", {"pts": 3, "w": 1, "d": 0, "l": 2, "gf": 3, "ga": 4, "gd": -1})]}


# ── export_group_stage_csv ───────────────────────────────────────────

def test_export_group_stage_csv(tmp_dir):
    path = os.path.join(tmp_dir, "test_grupos.csv")
    preds = [_dummy_prediction()]
    export_group_stage_csv(preds, path)
    assert os.path.exists(path)
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "Equipo Local" in headers
        rows = list(reader)
        assert len(rows) == 1


# ── export_group_stage_json ──────────────────────────────────────────

def test_export_group_stage_json(tmp_dir):
    path = os.path.join(tmp_dir, "test_grupos.json")
    preds = [_dummy_prediction()]
    export_group_stage_json(preds, path)
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["team_a"] == "Argentina"


# ── export_group_tables_csv ──────────────────────────────────────────

def test_export_group_tables_csv(tmp_dir):
    path = os.path.join(tmp_dir, "test_tablas.csv")
    gr = _dummy_group_results()
    export_group_tables_csv(gr, path)
    assert os.path.exists(path)
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "Equipo" in headers
        rows = list(reader)
        assert len(rows) >= 2


# ── export_knockout_csv ──────────────────────────────────────────────

def test_export_knockout_csv(tmp_dir):
    path = os.path.join(tmp_dir, "test_ko.csv")
    preds = [_dummy_prediction(round_name="R32")]
    export_knockout_csv(preds, path)
    assert os.path.exists(path)
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "Ronda" in headers

# ── export_knockout_json ─────────────────────────────────────────────

def test_export_knockout_json(tmp_dir):
    path = os.path.join(tmp_dir, "test_ko.json")
    preds = [_dummy_prediction(round_name="QF")]
    export_knockout_json(preds, path)
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data[0]["round"] == "QF"

# ── export_full_prode_csv ────────────────────────────────────────────

def test_export_full_prode_csv(tmp_dir):
    path = os.path.join(tmp_dir, "test_prode.csv")
    gp = [_dummy_prediction()]
    gr = _dummy_group_results()
    ko = [_dummy_prediction(round_name="Final")]
    export_full_prode_csv(gp, gr, ko, path)
    assert os.path.exists(path)
    with open(path, encoding="utf-8-sig") as f:
        content = f.read()
        assert "Campeon" in content or "FINAL" in content or "Grupo" in content

# ── export_all ───────────────────────────────────────────────────────

def test_export_all(tmp_dir):
    gp = [_dummy_prediction()]
    gr = _dummy_group_results()
    ko = [_dummy_prediction(round_name="Final")]
    export_all(gp, gr, ko)
    files = [os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir)]
    assert len(files) >= 6
