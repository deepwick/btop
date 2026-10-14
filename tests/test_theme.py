import re
import shutil
from pathlib import Path

import pytest

from deepwick_spec.ansi import runs
from deepwick_spec.check_port import check_port
from deepwick_spec.palette import load_palette
from deepwick_spec.tui import capture, tmux_available

REPO = Path(__file__).resolve().parents[1]
PALETTE = load_palette()
C = PALETTE.colors
BTOP_KEYS = {
    "main_bg", "main_fg", "title", "hi_fg", "selected_bg", "selected_fg", "inactive_fg", "graph_text",
    "meter_bg", "proc_misc", "cpu_box", "mem_box", "net_box", "proc_box", "div_line",
    *(f"{g}_{s}" for g in ("temp", "cpu", "free", "cached", "available", "used", "download", "upload", "process")
      for s in ("start", "mid", "end")),
}
EXPECTED = {
    "main_bg": "background", "main_fg": "foreground", "title": "foreground", "hi_fg": "blue",
    "selected_bg": "selection", "selected_fg": "foreground", "inactive_fg": "muted", "graph_text": "comment",
    "meter_bg": "overlay", "proc_misc": "teal", "cpu_box": "blue", "mem_box": "green", "net_box": "magenta",
    "proc_box": "teal", "div_line": "overlay",
    "cpu_start": "blue", "cpu_mid": "yellow", "cpu_end": "red",
    "temp_start": "blue", "temp_mid": "yellow", "temp_end": "red",
    "process_start": "blue", "process_mid": "yellow", "process_end": "red",
}


def theme():
    entries = re.findall(r'^theme\[([a-z_]+)\]="(#[0-9A-Fa-f]{6})"$', (REPO / "deepwick.theme").read_text(), re.M)
    return dict(entries)


def test_defines_every_btop_key():
    assert set(theme()) == BTOP_KEYS


def test_role_colors():
    t = theme()
    for key, color in EXPECTED.items():
        assert t[key] == C[color], key


@pytest.mark.skipif(not (tmux_available() and shutil.which("btop")), reason="requires tmux and btop")
def test_btop_renders_with_deepwick(tmp_path):
    config = tmp_path / "config" / "btop"
    (config / "themes").mkdir(parents=True)
    shutil.copy(REPO / "deepwick.theme", config / "themes" / "deepwick.theme")
    (config / "btop.conf").write_text('color_theme = "deepwick"\ntruecolor = True\n')
    env = {"XDG_CONFIG_HOME": str(tmp_path / "config"), "XDG_STATE_HOME": str(tmp_path / "state"), "XDG_CACHE_HOME": str(tmp_path / "cache")}
    text = capture("btop", env, size=(120, 40), wait_for="cpu")
    assert (tmp_path / "state" / "btop.log").exists() or not (Path.home() / ".local/state/btop.log").exists()
    styles = [s for _, s in runs(text)]
    assert any(s["bg"] == C["background"].lower() for s in styles)
    assert any(s["fg"] == C["blue"].lower() for s in styles)


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []
