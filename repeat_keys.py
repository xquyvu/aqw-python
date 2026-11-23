"""Repeat 1 2 3 2 3 5 in the focused window, with 200 ms between presses."""

import ctypes
import sys
import time
from ctypes import wintypes

SEQUENCE = (
    1,
    2,
    3,
    4,
    5,
)
DELAY = 0.075
VK_ESCAPE = 0x1B
ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUTUNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", wintypes.DWORD), ("data", INPUTUNION)]


def press_key(user32, number):
    virtual_key = ord(str(number))
    events = (INPUT * 2)(
        INPUT(type=1, ki=KEYBDINPUT(wVk=virtual_key)),
        INPUT(type=1, ki=KEYBDINPUT(wVk=virtual_key, dwFlags=0x0002)),
    )
    if user32.SendInput(2, events, ctypes.sizeof(INPUT)) != 2:
        raise RuntimeError(
            "Could not send the key press. Windows may block input to "
            "a window running with higher privileges."
        )


def wait_or_stop(user32, seconds):
    deadline = time.monotonic() + seconds
    while True:
        if user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(0.01, remaining))


def main():
    if sys.platform != "win32":
        raise SystemExit("This script requires Windows.")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    user32.SendInput.restype = wintypes.UINT
    user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
    user32.GetAsyncKeyState.restype = wintypes.SHORT

    print("Starting in 3 seconds. Focus the target window. Press Esc to stop.")
    try:
        if wait_or_stop(user32, 3):
            return
        while True:
            for number in SEQUENCE:
                press_key(user32, number)
                if wait_or_stop(user32, DELAY):
                    return
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopped.")


if __name__ == "__main__":
    main()
