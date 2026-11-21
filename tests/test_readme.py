"""Execute the two stage-relevant script-style README examples, not doctest."""
from pathlib import Path
import re
import unittest


class ReadmeTests(unittest.TestCase):
    def test_pacing_examples(self):
        text = Path("README.md").read_text()
        sections = ["## First useful example", "### More hand-checkable pacing examples"]
        blocks = []
        for section in sections:
            start = text.index(section)
            code = re.search(r"```python\n(.*?)\n```", text[start:], re.S)
            self.assertIsNotNone(code, section)
            blocks.append(code.group(1))
        self.assertEqual(len(blocks), 2)
        for index, code in enumerate(blocks):
            with self.subTest(example=index):
                exec(compile(code, f"README pacing example {index+1}", "exec"), {})
