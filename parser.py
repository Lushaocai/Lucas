from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import re
from typing import Any, List, Optional


class ParseError(ValueError):
    def __init__(self, message: str, line_no: Optional[int] = None, line: Optional[str] = None):
        prefix = f"Line {line_no}: " if line_no is not None else ""
        suffix = f" -> {line}" if line is not None else ""
        super().__init__(f"{prefix}{message}{suffix}")


@dataclass
class MaterialItem:
    material_type: str
    box_no: int
    amount: float


@dataclass
class AddMaterialCommand:
    code: str
    items: List[MaterialItem]


@dataclass
class PourCommand:
    code: str
    size: str
    vibration_time: Optional[float] = None


@dataclass
class LidCommand:
    code: str
    action: str


@dataclass
class StirCommand:
    code: str
    action_mode: str
    count: Optional[int] = None
    first_direction: Optional[str] = None
    first_speed: Optional[int] = None
    second_direction: Optional[str] = None
    second_speed: Optional[int] = None


@dataclass
class TemperatureCommand:
    code: str
    temperature: int


@dataclass
class WaitCommand:
    code: str
    target_temperature: Optional[int] = None
    delay_ms: Optional[int] = None


_AMOUNT_RE = re.compile(r"^A(\d+(?:\.\d+)?)$")
_TEMP_RE = re.compile(r"^C(\d+)$")
_DELAY_RE = re.compile(r"^D(\d+)$")
_COUNT_RE = re.compile(r"^S(\d+)$")
_SPEED_RE = re.compile(r"^([FR])(\d+)$")


def _to_float(value: str, label: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ParseError(f"Invalid {label}: {value}") from exc


def _to_int(value: str, label: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ParseError(f"Invalid {label}: {value}") from exc


def _parse_direction_speed(tokens: List[str], idx: int) -> tuple[str, int, int]:
    if idx >= len(tokens):
        raise ParseError("Missing direction/speed")
    token = tokens[idx]
    m = _SPEED_RE.match(token)
    if m:
        return m.group(1), int(m.group(2)), idx + 1

    direction = token
    if direction not in {"F", "R"}:
        raise ParseError(f"Invalid direction: {direction}")
    if idx + 1 >= len(tokens):
        raise ParseError("Missing speed")
    speed = _to_int(tokens[idx + 1], "speed")
    if speed < 0:
        raise ParseError("Speed must be >= 0")
    return direction, speed, idx + 2


def parse_line(line: str) -> Any:
    tokens = line.split()
    if not tokens:
        raise ParseError("Empty command")

    code = tokens[0].upper()
    args = tokens[1:]

    if code == "A01":
        if len(args) == 0 or len(args) % 3 != 0:
            raise ParseError("A01 expects groups of: <P|L> <box_no> <Aamount>")
        items: List[MaterialItem] = []
        for i in range(0, len(args), 3):
            material_type = args[i].upper()
            if material_type not in {"P", "L"}:
                raise ParseError(f"A01 invalid material type: {material_type}")
            box_no = _to_int(args[i + 1], "box number")
            if not 1 <= box_no <= 99:
                raise ParseError("A01 box number must be in [1, 99]")
            amount_token = args[i + 2].upper()
            m = _AMOUNT_RE.match(amount_token)
            if not m:
                raise ParseError(f"A01 invalid amount token: {amount_token}")
            amount = float(m.group(1))
            if amount <= 0:
                raise ParseError("A01 amount must be > 0")
            items.append(MaterialItem(material_type=material_type, box_no=box_no, amount=amount))
        return AddMaterialCommand(code=code, items=items)

    if code == "P01":
        if not args:
            raise ParseError("P01 expects at least <S|B>")
        size = args[0].upper()
        if size not in {"S", "B"}:
            raise ParseError("P01 size must be S or B")
        vibration_time: Optional[float] = None
        if len(args) > 1:
            raw = args[1].upper()
            if raw.startswith("D"):
                raw = raw[1:]
            vibration_time = _to_float(raw, "vibration time")
            if vibration_time < 0:
                raise ParseError("P01 vibration time must be >= 0")
        if len(args) > 2:
            raise ParseError("P01 has too many arguments")
        return PourCommand(code=code, size=size, vibration_time=vibration_time)

    if code == "C01":
        if len(args) != 1:
            raise ParseError("C01 expects exactly one action: O or C")
        action = args[0].upper()
        if action not in {"O", "C"}:
            raise ParseError("C01 action must be O or C")
        return LidCommand(code=code, action=action)

    if code == "S01":
        direction, speed, idx = _parse_direction_speed(args, 0)
        action_mode = "A"
        count: Optional[int] = None
        if idx < len(args):
            action_token = args[idx].upper()
            if action_token == "A":
                action_mode = "A"
            else:
                m = _COUNT_RE.match(action_token)
                if not m:
                    raise ParseError("S01 action must be A or S<count>")
                action_mode = "S"
                count = int(m.group(1))
                if count <= 0:
                    raise ParseError("S01 count must be > 0")
            idx += 1
        if idx != len(args):
            raise ParseError("S01 has too many arguments")
        return StirCommand(
            code=code,
            action_mode=action_mode,
            count=count,
            first_direction=direction,
            first_speed=speed,
        )

    if code == "S02":
        d1, s1, idx = _parse_direction_speed(args, 0)
        d2, s2, idx = _parse_direction_speed(args, idx)
        action_mode = "A"
        count: Optional[int] = None
        if idx < len(args):
            action_token = args[idx].upper()
            if action_token == "A":
                action_mode = "A"
            else:
                m = _COUNT_RE.match(action_token)
                if not m:
                    raise ParseError("S02 action must be A or S<count>")
                action_mode = "S"
                count = int(m.group(1))
                if count <= 0:
                    raise ParseError("S02 count must be > 0")
            idx += 1
        if idx != len(args):
            raise ParseError("S02 has too many arguments")
        return StirCommand(
            code=code,
            action_mode=action_mode,
            count=count,
            first_direction=d1,
            first_speed=s1,
            second_direction=d2,
            second_speed=s2,
        )

    if code == "S03":
        if args:
            raise ParseError("S03 takes no arguments")
        return StirCommand(code=code, action_mode="STOP")

    if code == "T01":
        if len(args) != 1:
            raise ParseError("T01 expects exactly one token: C<temp>")
        m = _TEMP_RE.match(args[0].upper())
        if not m:
            raise ParseError("T01 token must be C<temp>")
        temp = int(m.group(1))
        return TemperatureCommand(code=code, temperature=temp)

    if code == "W01":
        if not args:
            raise ParseError("W01 expects at least one of C<temp> or D<delay>")
        target_temperature: Optional[int] = None
        delay_ms: Optional[int] = None
        for token in args:
            up = token.upper()
            temp_match = _TEMP_RE.match(up)
            delay_match = _DELAY_RE.match(up)
            if temp_match:
                target_temperature = int(temp_match.group(1))
                continue
            if delay_match:
                delay_ms = int(delay_match.group(1))
                continue
            raise ParseError(f"W01 invalid token: {token}")
        return WaitCommand(code=code, target_temperature=target_temperature, delay_ms=delay_ms)

    raise ParseError(f"Unsupported command code: {code}")


def parse_program(source: str) -> List[Any]:
    commands: List[Any] = []
    for i, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].split(";", 1)[0].strip()
        if not line:
            continue
        try:
            commands.append(parse_line(line))
        except ParseError as exc:
            raise ParseError(str(exc), line_no=i, line=raw_line.rstrip("\n")) from exc
    return commands


def to_jsonable(commands: List[Any]) -> List[dict[str, Any]]:
    return [asdict(c) for c in commands]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parser for G-code-like feed program")
    parser.add_argument("file", help="Program file path")
    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        program = f.read()
    parsed = parse_program(program)
    print(json.dumps(to_jsonable(parsed), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
