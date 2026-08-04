"""Tests for :mod:`octopussy.manuscript_variables` (+ the live token gate)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from octopussy import manuscript_variables as mv

ROOT = Path(__file__).resolve().parents[1]
TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        mv.load_manuscript_config("/nonexistent/config.yaml")


def test_load_config_non_mapping(tmp_path):
    bad = tmp_path / "config.yaml"
    bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mv.load_manuscript_config(bad)


def test_generate_variables_shape():
    variables = mv.generate_variables(now=mv.datetime(2026, 8, 4, 12, 0, tzinfo=mv.timezone.utc))
    assert variables["FABERGE_IDENTITY"] == "Octopussy"
    assert variables["FABERGE_CODENAME"] == "FABERGÉ"
    assert variables["FABERGE_SEED"] == "7"
    assert variables["FABERGE_FLAGGED_FORGERY"].isdigit()
    assert variables["FABERGE_LOGISTICS_TRAINS"].isdigit()
    assert variables["GENERATION_TIMESTAMP"].startswith("2026-08-04T12:00:00")


def test_generate_variables_uses_config_path(tmp_path):
    import shutil

    shutil.copy(ROOT / "manuscript" / "config.yaml", tmp_path / "config.yaml")
    variables = mv.generate_variables(config_path=tmp_path / "config.yaml")
    assert variables["FABERGE_TITLE"].startswith("Octopussy")


def test_resolve_manuscript_tree_writes_files(tmp_path):
    variables = {"FABERGE_CODENAME": "FABERGÉ", "FABERGE_SEED": "7"}
    source = tmp_path / "ms"
    source.mkdir()
    (source / "00_intro.md").write_text("token {{FABERGE_CODENAME}} seed {{FABERGE_SEED}}\n", encoding="utf-8")
    (source / "03_results.md").write_text("{{FABERGE_CODENAME}}\n", encoding="utf-8")
    # A sidecar is ignored by the glob.
    (source / "SYNTAX.md").write_text("{{UNRESOLVED}}\n", encoding="utf-8")
    out_dir, resolved = mv.resolve_manuscript_tree(variables, manuscript_dir=source, output_dir=tmp_path / "out")
    assert resolved == ["00_intro.md", "03_results.md"]
    text = (tmp_path / "out" / "00_intro.md").read_text(encoding="utf-8")
    assert "FABERGÉ" in text and "{{" not in text


def test_resolve_manuscript_tree_strict_rejects_unresolved(tmp_path):
    variables = {}
    source = tmp_path / "ms"
    source.mkdir()
    (source / "00_intro.md").write_text("{{MISSING_TOKEN}}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mv.resolve_manuscript_tree(variables, manuscript_dir=source, output_dir=tmp_path / "out")


def test_live_token_cross_reference():
    """Every {{TOKEN}} in a numbered manuscript section must be generated."""
    variables = mv.generate_variables(now=mv.datetime(2026, 8, 4, 12, 0, tzinfo=mv.timezone.utc))
    for source in sorted((ROOT / "manuscript").glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token in TOKEN_RE.findall(text):
            assert token in variables, f"unresolved token {token} in {source.name}"
