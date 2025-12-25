from __future__ import annotations

from typing import Iterable, List


VK_CODE = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "pause": 0x13,
    "capslock": 0x14,
    "esc": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "delete": 0x2E,
    "0": 0x30,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,
    "a": 0x41,
    "b": 0x42,
    "c": 0x43,
    "d": 0x44,
    "e": 0x45,
    "f": 0x46,
    "g": 0x47,
    "h": 0x48,
    "i": 0x49,
    "j": 0x4A,
    "k": 0x4B,
    "l": 0x4C,
    "m": 0x4D,
    "n": 0x4E,
    "o": 0x4F,
    "p": 0x50,
    "q": 0x51,
    "r": 0x52,
    "s": 0x53,
    "t": 0x54,
    "u": 0x55,
    "v": 0x56,
    "w": 0x57,
    "x": 0x58,
    "y": 0x59,
    "z": 0x5A,
    "lshift": 0xA0,
    "rshift": 0xA1,
    "lctrl": 0xA2,
    "rctrl": 0xA3,
    "lalt": 0xA4,
    "ralt": 0xA5,
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
}

KEY_ALIASES = {
    "escape": "esc",
    "return": "enter",
    "control": "ctrl",
    "lcontrol": "lctrl",
    "rcontrol": "rctrl",
    "option": "alt",
}

EXTENDED_KEYS = {
    "up",
    "down",
    "left",
    "right",
    "insert",
    "delete",
    "home",
    "end",
    "pageup",
    "pagedown",
    "rctrl",
    "ralt",
}

MOUSE_BUTTON_FLAGS = {
    "left": (0x0002, 0x0004, 0),
    "right": (0x0008, 0x0010, 0),
    "middle": (0x0020, 0x0040, 0),
    "x1": (0x0080, 0x0100, 0x0001),
    "x2": (0x0080, 0x0100, 0x0002),
}

MOUSE_BUTTON_VK = {
    "left": 0x01,
    "right": 0x02,
    "middle": 0x04,
    "x1": 0x05,
    "x2": 0x06,
}

DEFAULT_MOUSE_BUTTONS = ["left", "right", "middle", "x1", "x2"]

_LETTER_KEYS = [chr(c) for c in range(ord("a"), ord("z") + 1)]
_DIGIT_KEYS = list("1234567890")
_FUNCTION_KEYS = [f"f{i}" for i in range(1, 13)]

DEFAULT_KM_KEYS = [
    "w",
    "a",
    "s",
    "d",
    "space",
    "shift",
    "ctrl",
    "alt",
    "tab",
    "esc",
    "enter",
    "backspace",
    "up",
    "down",
    "left",
    "right",
] + _DIGIT_KEYS + [k for k in _LETTER_KEYS if k not in {"w", "a", "s", "d"}] + _FUNCTION_KEYS


def normalize_key(name: str) -> str:
    key = name.strip().lower()
    return KEY_ALIASES.get(key, key)


def normalize_mouse_button(name: str) -> str:
    button = name.strip().lower()
    if button in {"mouse1", "button1"}:
        return "left"
    if button in {"mouse2", "button2"}:
        return "right"
    if button in {"mouse3", "button3"}:
        return "middle"
    if button in {"mouse4", "button4"}:
        return "x1"
    if button in {"mouse5", "button5"}:
        return "x2"
    return button


def parse_key_list(raw: str | None, default: Iterable[str]) -> List[str]:
    if not raw:
        return list(default)
    tokens = [t for t in raw.replace(",", " ").split(" ") if t.strip()]
    keys: List[str] = []
    for token in tokens:
        norm = normalize_key(token)
        if norm in VK_CODE and norm not in keys:
            keys.append(norm)
    return keys


def parse_mouse_button_list(raw: str | None, default: Iterable[str]) -> List[str]:
    if not raw:
        return list(default)
    tokens = [t for t in raw.replace(",", " ").split(" ") if t.strip()]
    buttons: List[str] = []
    for token in tokens:
        norm = normalize_mouse_button(token)
        if norm in MOUSE_BUTTON_FLAGS and norm not in buttons:
            buttons.append(norm)
    return buttons
