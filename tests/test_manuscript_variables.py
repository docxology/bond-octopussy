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


def test_detector_token_is_derived_from_the_mission_grid():
    """FABERGE_NUM_DETECTORS must track the real grid, not a frozen literal.

    Regression: the token was produced by a helper that returned a hardcoded
    100, so changing the mission lattice would have left the manuscript
    quoting a detector count the code no longer used.
    """
    from octopussy import mission

    variables = mv.generate_variables()
    assert int(variables["FABERGE_NUM_DETECTORS"]) == mission.SWEEP_GRID.nx * mission.SWEEP_GRID.ny
    assert int(variables["FABERGE_GRID_NX"]) == mission.SWEEP_GRID.nx
    assert int(variables["FABERGE_GRID_NY"]) == mission.SWEEP_GRID.ny
    assert int(variables["FABERGE_NUM_PIPELINES"]) == mission.PIPELINE_COUNT


def _modern_fraction(artifact, library) -> float:
    total = sum(w for _, w in artifact.mixture)
    modern = sum(w for p, w in artifact.mixture if library[p].introduced > artifact.claimed_year)
    return modern / total


def test_borderline_anachronism_picks_the_least_modern_fake():
    """The borderline case must be read off the exhibit, not asserted in prose."""
    from octopussy import forgery_detection as fg

    name, claimed, gap, modern = mv.borderline_anachronism()
    artifact = next(a for a in fg.DEFAULT_EXHIBIT if a.name == name)
    assert artifact.claimed_year == claimed

    fractions = {
        a.name: _modern_fraction(a, fg.PIGMENT_LIBRARY)
        for a in fg.DEFAULT_EXHIBIT
        if _modern_fraction(a, fg.PIGMENT_LIBRARY) > 0.0
    }
    assert modern == pytest.approx(min(fractions.values()))
    assert modern == pytest.approx(fractions[name])
    # The point of the case: it is a fake, but NOT the trivially-modern one.
    assert 0.0 < modern < 1.0, "the borderline case must not be an all-modern composition"
    assert gap == min(
        fg.PIGMENT_LIBRARY[p].introduced - claimed
        for p, _ in artifact.mixture
        if fg.PIGMENT_LIBRARY[p].introduced > claimed
    )


def test_borderline_case_is_actually_flagged_by_the_screen():
    """The results prose claims this artifact is still caught — prove it."""
    import numpy as np

    from octopussy import forgery_detection as fg

    name, _, _, _ = mv.borderline_anachronism()
    artifact = next(a for a in fg.DEFAULT_EXHIBIT if a.name == name)
    verdict = fg.screen_artifact(artifact, rng=np.random.default_rng(7))
    assert verdict.level in (fg.ForgeryLevel.LIKELY_FORGED, fg.ForgeryLevel.FORGED)


def test_borderline_anachronism_raises_when_exhibit_is_clean():
    """No anachronism anywhere must fail loudly, not return a silent default."""
    from octopussy import forgery_detection as fg

    honest = tuple(a for a in fg.DEFAULT_EXHIBIT if a.name == "tsar_egg")
    assert honest, "fixture precondition: an era-consistent artifact exists in the exhibit"
    assert _modern_fraction(honest[0], fg.PIGMENT_LIBRARY) == 0.0
    with pytest.raises(ValueError, match="no anachronistic pigment"):
        mv.borderline_anachronism(honest)


def test_generated_tokens_are_all_consumed_or_infrastructural():
    """Guard the reverse direction: a token nobody uses is dead weight."""
    variables = mv.generate_variables()
    used: set[str] = set()
    for source in sorted((ROOT / "manuscript").glob("[0-9][0-9]_*.md")):
        used.update(TOKEN_RE.findall(source.read_text(encoding="utf-8")))
    unused = sorted(set(variables) - used)
    assert unused == [], f"tokens generated but never referenced by a section: {unused}"


BIB_KEY_RE = re.compile(r"^@\w+\{([^,]+),", re.MULTILINE)
CITE_RE = re.compile(r"@([A-Za-z][A-Za-z0-9_:.#$%&+?<>~/-]*\d{4}[A-Za-z0-9]*)")


def _section_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted((ROOT / "manuscript").glob("[0-9][0-9]_*.md")))


def test_bibliography_and_citations_agree():
    """Both directions: no dangling citation, no uncited entry.

    A one-way check would let an unused (and therefore unreviewed) reference
    sit in the bibliography forever, which is exactly how a fabricated source
    survives.
    """
    bib = (ROOT / "manuscript" / "references.bib").read_text(encoding="utf-8")
    keys = set(BIB_KEY_RE.findall(bib))
    assert keys, "references.bib parsed to zero entries — the check would be vacuous"

    cited = set(CITE_RE.findall(_section_text()))
    assert cited, "no citations found in any numbered section — the check would be vacuous"

    assert cited - keys == set(), f"cited but missing from references.bib: {sorted(cited - keys)}"
    assert keys - cited == set(), f"in references.bib but never cited: {sorted(keys - cited)}"


def test_no_bare_metric_numerals_in_results_prose():
    """Results/abstract/conclusion prose must state metrics as tokens only.

    Strips code spans, resolved-token spans, figure syntax and section markup,
    then rejects any surviving standalone numeral. Catches the class of drift
    where a measured value is typed into prose and silently goes stale.
    """
    token_span = re.compile(r"\{\{[A-Z0-9_]+\}\}")
    for name in ("00_abstract.md", "03_results.md", "04_conclusion.md"):
        text = (ROOT / "manuscript" / name).read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"`[^`\n]*`", "", text)
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)\{[^}]*\}", "", text, flags=re.DOTALL)
        text = token_span.sub("", text)
        stray = re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", text)
        assert stray == [], f"hand-authored numeral(s) {stray} in {name}: use a manuscript token"


def test_worst_scoring_artifact_really_is_all_modern():
    """The prose calls the worst-scoring artifact 'the all-modern composition'.

    That adjective is not injected, so bind it: the artifact named by
    FABERGE_FORGERY_WORST must in fact be 100% post-claimed-year by weight.
    """
    from octopussy import forgery_detection as fg

    variables = mv.generate_variables()
    worst = next(a for a in fg.DEFAULT_EXHIBIT if a.name == variables["FABERGE_FORGERY_WORST"])
    assert _modern_fraction(worst, fg.PIGMENT_LIBRARY) == pytest.approx(1.0)


def test_station_count_token_matches_the_real_network():
    from octopussy import cover_logistics as cl

    variables = mv.generate_variables()
    assert int(variables["FABERGE_NUM_STATIONS"]) == len(cl.RailNetwork().nodes)
    assert int(variables["FABERGE_NUM_SEGMENTS"]) == cl.SEGMENT_COUNT


def test_borderline_anachronism_skips_zero_weight_mixture():
    """An artifact whose weights sum to zero has no meaningful fraction."""
    from octopussy import forgery_detection as fg

    weightless = fg.Artifact("weightless", 1900, (("titanium_white", 0.0),))
    with pytest.raises(ValueError, match="no anachronistic pigment"):
        mv.borderline_anachronism((weightless,))


def test_borderline_anachronism_keeps_the_best_when_a_worse_one_follows():
    """Scan order must not decide the answer."""
    from octopussy import forgery_detection as fg

    forward = mv.borderline_anachronism(fg.DEFAULT_EXHIBIT)
    reverse = mv.borderline_anachronism(tuple(reversed(fg.DEFAULT_EXHIBIT)))
    assert forward == reverse


def test_generate_variables_rejects_non_mapping_paper_section(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("paper:\n  - not\n  - a mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="'paper' section must be a mapping"):
        mv.generate_variables(config_path=config)
