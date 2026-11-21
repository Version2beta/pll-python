"""Stage acceptance aggregate. Complete; do not change."""
import unittest


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromNames(["tests.test_models", "tests.test_readme", "tests.test_effects"])
