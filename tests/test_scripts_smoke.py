"""Subprocess smoke tests for the thin mission-phase CLIs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_mission_brief_exit_zero():
    result = _run("mission_brief.py")
    assert result.returncode == 0
    assert "FABERGÉ" in result.stdout
    assert "octopussy" in result.stdout


def test_mission_recon_exit_zero():
    result = _run("mission_recon.py", "survey the hall")
    assert result.returncode == 0
    assert "survey the hall" in result.stdout


def test_mission_plan_exit_zero():
    result = _run("mission_plan.py")
    assert result.returncode == 0
    assert "forge_screen" in result.stdout and "concealed_sweep" in result.stdout


def test_mission_execute_writes_artifacts():
    result = _run("mission_execute.py")
    assert result.returncode == 0
    outcome_file = PROJECT_ROOT / "output" / "data" / "mission_outcome.json"
    assert outcome_file.is_file()
    payload = json.loads(outcome_file.read_text(encoding="utf-8"))
    assert payload["success"] is True
    assert set(payload["results"]) == {"forgery", "logistics", "concealment"}
    assert payload["provenance"]["seed"] == 7
    assert (PROJECT_ROOT / "output" / "figures" / "forgery_fingerprints.png").is_file()


def test_mission_debrief_exit_zero():
    result = _run("mission_debrief.py")
    assert result.returncode == 0
    assert "lessons learned" in result.stdout


def test_demo_mission_runs_full_lifecycle():
    result = _run("demo_mission.py")
    assert result.returncode == 0
    assert "full mission lifecycle" in result.stdout
    assert "success: True" in result.stdout


def test_z_generate_writes_variables_and_manuscript(tmp_path):
    # Run against a fresh repo copy to avoid mutating tracked state.
    import shutil

    work = tmp_path / "pkg"
    shutil.copytree(PROJECT_ROOT, work, ignore=shutil.ignore_patterns(".git", ".venv", "output", "*.egg-info"))
    result = subprocess.run(
        [sys.executable, str(work / "scripts" / "z_generate_manuscript_variables.py")],
        cwd=work,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr
    variables = json.loads((work / "output" / "data" / "manuscript_variables.json").read_text(encoding="utf-8"))
    assert variables["FABERGE_CODENAME"] == "FABERGÉ"
    resolved = (work / "output" / "manuscript" / "00_abstract.md").read_text(encoding="utf-8")
    assert "{{" not in resolved
