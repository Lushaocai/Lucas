import unittest

from parser import (
    AddMaterialCommand,
    LidCommand,
    ParseError,
    PourCommand,
    StirCommand,
    TemperatureCommand,
    WaitCommand,
    parse_line,
    parse_program,
)


class ParserTests(unittest.TestCase):
    def test_a01_multi_items(self):
        cmd = parse_line("A01 P 01 A1000.000 L 03 A500")
        self.assertIsInstance(cmd, AddMaterialCommand)
        self.assertEqual(len(cmd.items), 2)
        self.assertEqual(cmd.items[0].material_type, "P")
        self.assertEqual(cmd.items[0].box_no, 1)
        self.assertEqual(cmd.items[0].amount, 1000.0)

    def test_p01(self):
        cmd = parse_line("P01 S D5.001")
        self.assertIsInstance(cmd, PourCommand)
        self.assertEqual(cmd.size, "S")
        self.assertAlmostEqual(cmd.vibration_time, 5.001)

    def test_c01(self):
        cmd = parse_line("C01 O")
        self.assertIsInstance(cmd, LidCommand)
        self.assertEqual(cmd.action, "O")

    def test_s01(self):
        cmd = parse_line("S01 F1000 S100")
        self.assertIsInstance(cmd, StirCommand)
        self.assertEqual(cmd.first_direction, "F")
        self.assertEqual(cmd.first_speed, 1000)
        self.assertEqual(cmd.action_mode, "S")
        self.assertEqual(cmd.count, 100)

    def test_s02(self):
        cmd = parse_line("S02 F1000 R1000 A")
        self.assertIsInstance(cmd, StirCommand)
        self.assertEqual(cmd.first_direction, "F")
        self.assertEqual(cmd.second_direction, "R")
        self.assertEqual(cmd.action_mode, "A")

    def test_s03(self):
        cmd = parse_line("S03")
        self.assertEqual(cmd.action_mode, "STOP")

    def test_t01(self):
        cmd = parse_line("T01 C200")
        self.assertIsInstance(cmd, TemperatureCommand)
        self.assertEqual(cmd.temperature, 200)

    def test_w01(self):
        cmd = parse_line("W01 C150 D1000")
        self.assertIsInstance(cmd, WaitCommand)
        self.assertEqual(cmd.target_temperature, 150)
        self.assertEqual(cmd.delay_ms, 1000)

    def test_program_and_comments(self):
        cmds = parse_program("""
        # comment
        A01 P 01 A200
        W01 D500 ; inline comment
        """)
        self.assertEqual(len(cmds), 2)

    def test_invalid_code(self):
        with self.assertRaises(ParseError):
            parse_line("X99 1 2 3")


if __name__ == "__main__":
    unittest.main()
