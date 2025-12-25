from __future__ import annotations

from typing import Any, Mapping, Set

from nitrogen.input.base import InputController
from nitrogen.input.keymap import (
    EXTENDED_KEYS,
    MOUSE_BUTTON_FLAGS,
    VK_CODE,
    normalize_key,
    normalize_mouse_button,
)

try:
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _SENDINPUT_AVAILABLE = True
except Exception:
    _user32 = None
    _SENDINPUT_AVAILABLE = False

try:
    import pyautogui
except Exception:  # pragma: no cover - optional fallback
    pyautogui = None



def _value_from_action(value: Any) -> int:
    if value is None:
        return 0
    if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        try:
            return int(value[0])
        except Exception:
            pass
    try:
        return int(value)
    except Exception:
        return 0


if _SENDINPUT_AVAILABLE:
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", wintypes.ULONG_PTR),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", wintypes.ULONG_PTR),
        ]

    class _INPUT_UNION(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
        ]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [
            ("type", wintypes.DWORD),
            ("u", _INPUT_UNION),
        ]

    INPUT_MOUSE = 0
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_EXTENDEDKEY = 0x0001
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_WHEEL = 0x0800


def _send_input(*inputs: "INPUT") -> None:
    if not _SENDINPUT_AVAILABLE:
        return
    n_inputs = len(inputs)
    if n_inputs == 0:
        return
    array = (INPUT * n_inputs)(*inputs)
    _user32.SendInput(n_inputs, array, ctypes.sizeof(INPUT))


class KeyboardMouseController(InputController):
    def __init__(
        self,
        dry_run: bool = False,
        backend: str = "sendinput",
        key_list: list[str] | None = None,
        mouse_buttons: list[str] | None = None,
    ) -> None:
        super().__init__(dry_run=dry_run)
        self.backend = backend
        self.pressed_keys: Set[str] = set()
        self.pressed_mouse_buttons: Set[str] = set()
        self.key_list = [normalize_key(k) for k in key_list] if key_list else None
        if self.key_list:
            self.key_list = [k for k in self.key_list if k in VK_CODE]
        self.mouse_button_list = [normalize_mouse_button(b) for b in mouse_buttons] if mouse_buttons else None
        if self.mouse_button_list:
            self.mouse_button_list = [b for b in self.mouse_button_list if b in MOUSE_BUTTON_FLAGS]

        if self.backend == "sendinput" and not _SENDINPUT_AVAILABLE:
            self.backend = "pyautogui"

        if self.backend == "pyautogui" and pyautogui is None:
            raise ImportError("pyautogui is required for the keyboard/mouse fallback backend.")

    def step(self, action: Mapping[str, Any]) -> None:
        desired_keys = self._extract_keys(action.get("keys", []))
        desired_buttons = self._extract_buttons(action.get("mouse_buttons", []))
        dx = _value_from_action(action.get("mouse_dx", 0))
        dy = _value_from_action(action.get("mouse_dy", 0))
        wheel = _value_from_action(action.get("mouse_wheel", 0))

        keys_to_release = self.pressed_keys - desired_keys
        keys_to_press = desired_keys - self.pressed_keys
        buttons_to_release = self.pressed_mouse_buttons - desired_buttons
        buttons_to_press = desired_buttons - self.pressed_mouse_buttons

        if not self.dry_run:
            for key in keys_to_release:
                self._key_event(key, is_down=False)
            for key in keys_to_press:
                self._key_event(key, is_down=True)
            for button in buttons_to_release:
                self._mouse_button_event(button, is_down=False)
            for button in buttons_to_press:
                self._mouse_button_event(button, is_down=True)
            if dx != 0 or dy != 0:
                self._mouse_move(dx, dy)
            if wheel != 0:
                self._mouse_wheel(wheel)

        self.pressed_keys = desired_keys
        self.pressed_mouse_buttons = desired_buttons

    def reset(self) -> None:
        if not self.dry_run:
            for key in list(self.pressed_keys):
                self._key_event(key, is_down=False)
            for button in list(self.pressed_mouse_buttons):
                self._mouse_button_event(button, is_down=False)
        self.pressed_keys.clear()
        self.pressed_mouse_buttons.clear()

    def _extract_keys(self, raw: Any) -> Set[str]:
        if isinstance(raw, Mapping):
            keys = {k for k, v in raw.items() if v}
        elif isinstance(raw, (list, tuple, set)):
            keys = set(raw)
        else:
            keys = set()
        if self.key_list and not isinstance(raw, Mapping):
            vector_keys = self._vector_to_names(raw, self.key_list)
            if vector_keys is not None:
                return vector_keys
        normalized = set()
        for key in keys:
            if not isinstance(key, str):
                continue
            name = normalize_key(key)
            if name in VK_CODE:
                normalized.add(name)
        return normalized

    def _extract_buttons(self, raw: Any) -> Set[str]:
        if isinstance(raw, Mapping):
            buttons = {k for k, v in raw.items() if v}
        elif isinstance(raw, (list, tuple, set)):
            buttons = set(raw)
        else:
            buttons = set()
        if self.mouse_button_list and not isinstance(raw, Mapping):
            vector_buttons = self._vector_to_names(raw, self.mouse_button_list)
            if vector_buttons is not None:
                return vector_buttons
        normalized = set()
        for button in buttons:
            if not isinstance(button, str):
                continue
            name = normalize_mouse_button(button)
            if name in MOUSE_BUTTON_FLAGS:
                normalized.add(name)
        return normalized

    @staticmethod
    def _vector_to_names(raw: Any, names: list[str]) -> Set[str] | None:
        if not hasattr(raw, "__len__"):
            return None
        try:
            if len(raw) != len(names):
                return None
            selected = set()
            for name, value in zip(names, raw):
                if float(value) > 0:
                    selected.add(name)
            return selected
        except Exception:
            return None

    def _key_event(self, key: str, is_down: bool) -> None:
        if self.backend == "pyautogui":
            if is_down:
                pyautogui.keyDown(key)
            else:
                pyautogui.keyUp(key)
            return

        vk = VK_CODE.get(key)
        if vk is None:
            return
        flags = 0
        if not is_down:
            flags |= KEYEVENTF_KEYUP
        if key in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY
        ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)
        _send_input(INPUT(type=INPUT_KEYBOARD, ki=ki))

    def _mouse_move(self, dx: int, dy: int) -> None:
        if self.backend == "pyautogui":
            pyautogui.moveRel(dx, dy, duration=0)
            return
        mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=0, dwFlags=MOUSEEVENTF_MOVE, time=0, dwExtraInfo=0)
        _send_input(INPUT(type=INPUT_MOUSE, mi=mi))

    def _mouse_button_event(self, button: str, is_down: bool) -> None:
        if self.backend == "pyautogui":
            if button not in {"left", "right", "middle"}:
                return
            if is_down:
                pyautogui.mouseDown(button=button)
            else:
                pyautogui.mouseUp(button=button)
            return
        down_flag, up_flag, data = MOUSE_BUTTON_FLAGS[button]
        flag = down_flag if is_down else up_flag
        mi = MOUSEINPUT(dx=0, dy=0, mouseData=data, dwFlags=flag, time=0, dwExtraInfo=0)
        _send_input(INPUT(type=INPUT_MOUSE, mi=mi))

    def _mouse_wheel(self, amount: int) -> None:
        if self.backend == "pyautogui":
            pyautogui.scroll(amount)
            return
        mi = MOUSEINPUT(dx=0, dy=0, mouseData=amount, dwFlags=MOUSEEVENTF_WHEEL, time=0, dwExtraInfo=0)
        _send_input(INPUT(type=INPUT_MOUSE, mi=mi))
