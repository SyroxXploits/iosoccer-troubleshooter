# IOSoccer Troubleshooter

Windows desktop troubleshooter for IOSoccer with one-click repair actions.

## What It Does

- Detects Steam path, IOSoccer app ID, and install directory
- Verifies game files through Steam
- Launches IOSoccer with safe or borderless parameters
- Resets IOSoccer registry settings with double confirmation
- Updates `mat_queue_mode` in `config.cfg` with backup
- Resets `config.cfg` from a template with backup
- Opens Windows sound, focus assist, and update settings
- Opens Steam uninstall/reinstall flows

## Main Source File

- `iosoccer_troubleshooter_ttk.py`

## Requirements

- Windows 10/11
- Python 3.10+

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run From Source

```powershell
python .\iosoccer_troubleshooter_ttk.py
```

## Build EXE

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "IOSoccer Troubleshooter" .\iosoccer_troubleshooter_ttk.py
```

Output:

- `dist/IOSoccer Troubleshooter.exe`

## Safety Notes

- Registry and folder deletion actions always require explicit confirmation.
- `config.cfg` actions create timestamped backups before writing changes.
