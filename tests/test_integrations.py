"""The installers and integrations/ must agree.

Every target an installer can write must have a real file under
integrations/<target>/, and scripts/install.sh and scripts/install.ps1 must
offer exactly the same target set. A target that is wired into one installer
but not the other, or that has no integration file, fails here.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SH = ROOT / "scripts" / "install.sh"
PS1 = ROOT / "scripts" / "install.ps1"
INTEGRATIONS = ROOT / "integrations"


def sh_targets():
    text = SH.read_text(encoding="utf-8")
    match = re.search(r'all\)\s*TARGETS="([^"]+)"', text)
    if match is None:
        raise AssertionError("install.sh has no 'all' target expansion")
    return [t.strip() for t in match.group(1).split(",") if t.strip()]


def ps1_targets():
    text = PS1.read_text(encoding="utf-8")
    match = re.search(r"\$AllTargets\s*=\s*@\(([^)]*)\)", text)
    if match is None:
        raise AssertionError("install.ps1 has no $AllTargets list")
    return re.findall(r"'([^']+)'", match.group(1))


class IntegrationsTest(unittest.TestCase):
    def test_installers_cover_the_same_targets(self):
        self.assertEqual(sh_targets(), ps1_targets())

    def test_targets_are_lowercase_hyphenated(self):
        for target in sh_targets():
            self.assertRegex(target, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def test_every_target_has_an_integration_directory_with_a_file(self):
        missing = []
        for target in sh_targets():
            folder = INTEGRATIONS / target
            if not folder.is_dir():
                missing.append(f"{target}: no integrations/{target}/ directory")
            elif not any(p.is_file() for p in folder.rglob("*")):
                missing.append(f"{target}: integrations/{target}/ has no file")
        self.assertEqual(missing, [], "installer targets lack integration files")

    def test_no_orphan_integration_directories(self):
        targets = set(sh_targets())
        orphaned = sorted(d.name for d in INTEGRATIONS.iterdir()
                          if d.is_dir() and d.name not in targets)
        self.assertEqual(orphaned, [], "integration directories with no installer target")


if __name__ == "__main__":
    unittest.main(verbosity=2)