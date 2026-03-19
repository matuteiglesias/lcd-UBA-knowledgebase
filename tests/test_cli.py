import unittest

from lcd_kb.cli import build_parser


class CliTests(unittest.TestCase):
    def test_fetch_parser(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["fetch", "--entity", "page"])
        self.assertEqual(args.command, "fetch")
        self.assertEqual(args.entity, "page")


if __name__ == "__main__":
    unittest.main()
