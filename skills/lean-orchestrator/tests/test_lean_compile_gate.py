#!/usr/bin/env python3
"""Regression tests for assets/lean-compile-gate.sh, using a stub compiler."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import time
import unittest

GATE = Path(__file__).resolve().parent.parent / "assets" / "lean-compile-gate.sh"
STUB = """#!/bin/bash
echo "start $(date +%s.%N) $(basename "$PWD") ${LEAN_GATE_SLOT:-none}" >> "$GATE_TEST_LOG"
sleep 0.6
echo "end $(date +%s.%N) $(basename "$PWD") ${LEAN_GATE_SLOT:-none}" >> "$GATE_TEST_LOG"
"""


@unittest.skipUnless(shutil.which("flock"), "flock not available")
class CompileGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        self.lean = bin_dir / "lean"
        shutil.copy(GATE, self.lean)
        (bin_dir / "lean.real").write_text(STUB)
        for path in (self.lean, bin_dir / "lean.real"):
            path.chmod(path.stat().st_mode | stat.S_IXUSR)
        for name in ("proj", "main", "other"):
            (self.tmp / name).mkdir()
        self.log = self.tmp / "log"
        self.env = dict(
            os.environ,
            LEAN_GATE_SLOTS="2",
            LEAN_GATE_PREFIXES=str(self.tmp / "proj"),
            LEAN_GATE_RESERVED=str(self.tmp / "main"),
            LEAN_GATE_DIR=str(self.tmp / "locks"),
            GATE_TEST_LOG=str(self.log),
        )
        self.env.pop("LEAN_GATE_SLOT", None)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def run_in(self, names: list[str], arg: str = "X.lean") -> None:
        procs = [
            subprocess.Popen([str(self.lean), arg], cwd=self.tmp / n, env=self.env,
                             stderr=subprocess.DEVNULL)
            for n in names
        ]
        for p in procs:
            self.assertEqual(p.wait(timeout=30), 0)

    def events(self) -> list[tuple[float, int, str, str]]:
        out = []
        for line in self.log.read_text().splitlines():
            kind, t, where, slot = line.split()
            out.append((float(t), 1 if kind == "start" else -1, where, slot))
        return sorted(out, key=lambda e: (e[0], e[1]))

    def max_concurrent(self, where: str) -> int:
        cur = best = 0
        for _, delta, w, _ in self.events():
            if w == where:
                cur += delta
                best = max(best, cur)
        return best

    def test_shared_slots_bound_project_compiles(self) -> None:
        self.run_in(["proj"] * 5)
        self.assertEqual(self.max_concurrent("proj"), 2)

    def test_reserved_checkout_is_not_blocked(self) -> None:
        start = time.monotonic()
        procs = [subprocess.Popen([str(self.lean), "X.lean"], cwd=self.tmp / "proj",
                                  env=self.env, stderr=subprocess.DEVNULL) for _ in range(2)]
        time.sleep(0.2)
        self.run_in(["main"])
        self.assertLess(time.monotonic() - start, 1.1)
        for p in procs:
            p.wait(timeout=30)
        slots = {s for _, d, w, s in self.events() if w == "main" and d == 1}
        self.assertEqual(slots, {"2"})

    def test_other_directories_and_non_compiles_are_ungated(self) -> None:
        self.run_in(["other"] * 3)
        self.assertEqual(self.max_concurrent("other"), 3)
        self.log.unlink()
        self.run_in(["proj"] * 3, arg="--version")
        self.assertEqual(self.max_concurrent("proj"), 3)


if __name__ == "__main__":
    unittest.main()
