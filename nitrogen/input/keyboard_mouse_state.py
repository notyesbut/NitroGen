from __future__ import annotations

import platform
import time
from typing import Dict, List, Optional, Tuple

from nitrogen.input.keymap import (
    MOUSE_BUTTON_VK,
    VK_CODE,
    normalize_key,
    normalize_mouse_button,
)

assert platform.system().lower() == "windows", "This module is only supported on Windows."

import win32api


class KeyboardMouseState:
    def __init__(
        self,
        keys: List[str],
        mouse_buttons: List[str],
        raw_mouse: Optional[object] = None,
    ) -> None:
        self.keys = []
        for key in keys:
            norm = normalize_key(key)
            if norm in VK_CODE and norm not in self.keys:
                self.keys.append(norm)
        self.mouse_buttons = []
        for button in mouse_buttons:
            norm = normalize_mouse_button(button)
            if norm in MOUSE_BUTTON_VK and norm not in self.mouse_buttons:
                self.mouse_buttons.append(norm)
        self._prev_pos = None
        self._raw_mouse = raw_mouse

    def sample(self) -> Dict[str, object]:
        keys_vec = []
        pressed_keys = []
        for key in self.keys:
            vk = VK_CODE[key]
            pressed = bool(win32api.GetAsyncKeyState(vk) & 0x8000)
            keys_vec.append(1 if pressed else 0)
            if pressed:
                pressed_keys.append(key)

        buttons_vec = []
        pressed_buttons = []
        for button in self.mouse_buttons:
            vk = MOUSE_BUTTON_VK[button]
            pressed = bool(win32api.GetAsyncKeyState(vk) & 0x8000)
            buttons_vec.append(1 if pressed else 0)
            if pressed:
                pressed_buttons.append(button)

        x, y = win32api.GetCursorPos()

        if self._raw_mouse is not None:
            try:
                dx, dy, wheel = self._raw_mouse.poll()
            except Exception:
                dx, dy, wheel = self._cursor_delta(x, y)
        else:
            dx, dy, wheel = self._cursor_delta(x, y)

        return {
            "timestamp": time.time(),
            "keys": pressed_keys,
            "keys_vec": keys_vec,
            "mouse_buttons": pressed_buttons,
            "mouse_buttons_vec": buttons_vec,
            "mouse_dx": int(dx),
            "mouse_dy": int(dy),
            "mouse_wheel": int(wheel),
            "mouse_pos": [int(x), int(y)],
        }

    def _cursor_delta(self, x: int, y: int) -> Tuple[int, int, int]:
        if self._prev_pos is None:
            dx = 0
            dy = 0
        else:
            dx = x - self._prev_pos[0]
            dy = y - self._prev_pos[1]
        self._prev_pos = (x, y)
        return int(dx), int(dy), 0
