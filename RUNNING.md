# Running NitroGen (Windows)

## Quick start

1) Start the inference server (uses NG_PT or PATH_TO_NG if set):

```bash
python scripts/serve.py
```

2) Run the agent:

```bash
python scripts/play.py --controller km
```

`--controller` can be `gamepad` or `km`.

## .env / environment variables

Recommended `.env` example:

```bash
NG_PT=C:\path\to\ng.pt
NG_PORT=5555
NG_PROCESS=Game.exe
NG_CONTROLLER=km
NG_KM_MOUSE_SENS=15
```

Supported variables:

- `NG_PT`: full path to `ng.pt`.
- `PATH_TO_NG`: directory containing `ng.pt`.
- `NG_PORT`: inference server port.
- `NG_PROCESS`: game executable name (e.g. `Game.exe`).
- `NG_CONTROLLER`: `gamepad` or `km`.
- `NG_KM_KEYS`: comma/space-separated key list for KM actions (overrides defaults).
- `NG_KM_MOUSE_BUTTONS`: comma/space-separated mouse buttons (left,right,middle,x1,x2).
- `NG_KM_MOUSE_SENS`: mouse sensitivity (pixels per step) for the gamepad->KM adapter.
- `NG_KM_DEADZONE`: deadzone for stick -> WASD mapping (default `0.2`).
- `NG_KM_MOUSE_MAX`: max mouse delta per step (default `50`).
- `NG_KM_TRIGGER_THRES`: trigger press threshold (default `0.1`).
- `NG_DISABLE_INPUT`: set to `1` to run in dry-run mode (no input is sent).
- `NG_STOP_FILE`: path to a stop file. If it exists, `play.py` exits the loop.
- `NG_ENABLE_SPEEDHACK`: set to `1` to enable xspeedhack (unsafe, off by default).

## Safety notes

- Safe mode is the default: no xspeedhack import, no process injection, only OS-level input and screen capture.
- Enabling `NG_ENABLE_SPEEDHACK=1` uses `xspeedhack` and is unsafe for anti-cheat.
- Prefer offline / non-competitive environments.

## KM adapter notes

The current model outputs gamepad actions. For KM control, `play.py` maps gamepad actions to keyboard/mouse (WASD + mouse) so it can run immediately. For best results, collect KM demonstrations and train a KM action head.

## KM recording

Record KM actions + frames for training:

```bash
python scripts/record_km.py --process Game.exe --fps 30
```

Outputs:
- `out/record_km/<run_id>/frames/*.png`
- `out/record_km/<run_id>/actions.jsonl`
- `out/record_km/<run_id>/meta.json`

Use `--keys` / `--mouse-buttons` (or `NG_KM_KEYS` / `NG_KM_MOUSE_BUTTONS`) to control which inputs are tracked.
Mouse wheel is currently recorded as `0` (no wheel hook).

Recording env vars:
- `NG_RECORD_FPS`: capture FPS.
- `NG_RECORD_MAX_FRAMES`: cap frames (0 = unlimited).
- `NG_RECORD_DURATION`: cap seconds (0 = unlimited).
- `NG_IMAGE_WIDTH` / `NG_IMAGE_HEIGHT`: recorded frame size.
- `NG_RECORD_RAW_MOUSE`: enable raw input mouse deltas + wheel (default on).

Flags:
- `--raw-mouse` / `--no-raw-mouse`: toggle raw input mouse capture.
