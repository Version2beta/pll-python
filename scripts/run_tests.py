"""Non-vacuous stdout unittest observations. Complete; do not change."""
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class Observed(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        print(f"PASS {test.id()}", flush=True)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_tests.py MODULE_OR_all EXPECTED_COUNT")
    name, expected = sys.argv[1], int(sys.argv[2])
    suite = (unittest.defaultTestLoader.discover("tests", top_level_dir=".")
             if name == "all" else unittest.defaultTestLoader.loadTestsFromName(name))
    if suite.countTestCases() != expected or expected < 1:
        raise SystemExit(f"test inventory mismatch: {suite.countTestCases()} != {expected}")
    result = unittest.TextTestRunner(verbosity=2, resultclass=Observed).run(suite)
    if (not result.wasSuccessful() or result.testsRun != expected or result.skipped
            or result.expectedFailures or result.unexpectedSuccesses):
        raise SystemExit(1)
    print(f"PASS COUNT {result.testsRun}", flush=True)


if __name__ == "__main__":
    main()
