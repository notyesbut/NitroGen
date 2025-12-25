from __future__ import annotations

import threading
from ctypes import wintypes
import ctypes


WM_INPUT = 0x00FF
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_MOUSEWHEEL = 0x020A
WM_QUIT = 0x0012

RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0

RIDEV_INPUTSINK = 0x00000100

RI_MOUSE_WHEEL = 0x0400
MOUSE_MOVE_ABSOLUTE = 0x0001

HWND_MESSAGE = wintypes.HWND(-3)

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


WNDPROC = ctypes.WINFUNCTYPE(
    wintypes.LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [
        ("usFlags", wintypes.USHORT),
        ("usButtonFlags", wintypes.USHORT),
        ("usButtonData", wintypes.USHORT),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    ]


class _RAWINPUT_DATA(ctypes.Union):
    _fields_ = [("mouse", RAWMOUSE)]


class RAWINPUT(ctypes.Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data", _RAWINPUT_DATA),
    ]


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class RawMouseHook:
    def __init__(self, capture_background: bool = True) -> None:
        self.capture_background = capture_background
        self._lock = threading.Lock()
        self._dx = 0
        self._dy = 0
        self._wheel = 0
        self._last_abs = None
        self._thread = None
        self._thread_id = None
        self._ready = threading.Event()
        self._error = None
        self._hwnd = None
        self._wnd_proc = None

    def start(self, timeout: float = 5.0) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=timeout):
            raise RuntimeError("Raw input thread failed to start.")
        if self._error:
            raise RuntimeError(self._error)

    def stop(self) -> None:
        if self._hwnd:
            _user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
        elif self._thread_id:
            _user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=1.0)
        self._thread = None

    def poll(self) -> tuple[int, int, int]:
        with self._lock:
            dx = self._dx
            dy = self._dy
            wheel = self._wheel
            self._dx = 0
            self._dy = 0
            self._wheel = 0
        return dx, dy, wheel

    def _run(self) -> None:
        self._thread_id = _kernel32.GetCurrentThreadId()
        class_name = "NitrogenRawInputWindow"

        self._wnd_proc = WNDPROC(self._handle_message)
        h_instance = _kernel32.GetModuleHandleW(None)
        wndclass = WNDCLASS()
        wndclass.lpfnWndProc = self._wnd_proc
        wndclass.hInstance = h_instance
        wndclass.lpszClassName = class_name
        _user32.RegisterClassW(ctypes.byref(wndclass))

        hwnd = _user32.CreateWindowExW(
            0,
            class_name,
            "Nitrogen Raw Input",
            0,
            0,
            0,
            0,
            0,
            HWND_MESSAGE,
            None,
            h_instance,
            None,
        )
        self._hwnd = hwnd
        if not hwnd:
            self._error = "CreateWindowExW failed."
            self._ready.set()
            return

        flags = RIDEV_INPUTSINK if self.capture_background else 0
        rid = RAWINPUTDEVICE(usUsagePage=0x01, usUsage=0x02, dwFlags=flags, hwndTarget=hwnd)
        if not _user32.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(rid)):
            self._error = "RegisterRawInputDevices failed."
            self._ready.set()
            return

        self._ready.set()

        msg = MSG()
        while _user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))

    def _handle_message(self, hwnd, msg, wparam, lparam):
        if msg == WM_INPUT:
            self._handle_raw_input(lparam)
            return 0
        if msg == WM_MOUSEWHEEL:
            delta = ctypes.c_short((wparam >> 16) & 0xFFFF).value
            with self._lock:
                self._wheel += int(delta)
            return 0
        if msg == WM_CLOSE:
            _user32.DestroyWindow(hwnd)
            return 0
        if msg == WM_DESTROY:
            _user32.PostQuitMessage(0)
            return 0
        return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _handle_raw_input(self, h_raw_input) -> None:
        size = wintypes.UINT(0)
        if _user32.GetRawInputData(
            h_raw_input,
            RID_INPUT,
            None,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER),
        ) == 0xFFFFFFFF:
            return
        if size.value == 0:
            return

        buf = ctypes.create_string_buffer(size.value)
        read_size = _user32.GetRawInputData(
            h_raw_input,
            RID_INPUT,
            buf,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER),
        )
        if read_size != size.value:
            return

        raw = ctypes.cast(buf, ctypes.POINTER(RAWINPUT)).contents
        if raw.header.dwType != RIM_TYPEMOUSE:
            return

        mouse = raw.data.mouse
        dx = int(mouse.lLastX)
        dy = int(mouse.lLastY)

        if mouse.usFlags & MOUSE_MOVE_ABSOLUTE:
            if self._last_abs is not None:
                dx = int(mouse.lLastX - self._last_abs[0])
                dy = int(mouse.lLastY - self._last_abs[1])
            self._last_abs = (int(mouse.lLastX), int(mouse.lLastY))

        wheel = 0
        if mouse.usButtonFlags & RI_MOUSE_WHEEL:
            wheel = ctypes.c_short(mouse.usButtonData).value

        with self._lock:
            self._dx += dx
            self._dy += dy
            self._wheel += int(wheel)
