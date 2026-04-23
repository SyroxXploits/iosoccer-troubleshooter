# IOSoccer Troubleshooter

Windows desktop utility for fixing common IOSoccer startup, crash, config, and launch issues.

The app is focused on practical repair actions that players usually do manually in Steam, Windows settings, and local game files.

## Features

- Auto-detects Steam path, IOSoccer App ID, and install directory
- Verifies IOSoccer files through Steam
- Launches IOSoccer in:
  - Safe mode (`-h 768 -w 1024 -windowed`)
  - Borderless mode (`-noborder -window`)
- Opens useful Windows settings directly:
  - Sound
  - Focus Assist
  - Windows Update
- Opens Steam uninstall/reinstall actions
- Resets IOSoccer registry settings with two-step confirmation
- Edits `mat_queue_mode` in `config.cfg` (with automatic backup)
- Resets `config.cfg` from template (with automatic backup)
- Optional install folder deletion with strict safety checks and confirmation

## Why This Exists

IOSoccer runs on an older Source-engine stack where issues can come from config state, registry state, launch parameters, audio devices, or local file corruption.

This tool gathers those fixes into one interface so players can apply them quickly and consistently.

## Project Structure

- `iosoccer_troubleshooter_ttk.py`: Main application (single-file GUI app)
- `requirements.txt`: Python dependencies
- `LICENSE`: MIT license

## Requirements

- Windows 10 or Windows 11
- Python 3.10+ recommended

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

Build output:

- `dist/IOSoccer Troubleshooter.exe`

## Action Reference

### Verify Files
Opens Steam validation for IOSoccer files.

### Launch Safe Mode Now
Launches with lower, windowed-safe startup parameters:

- `-h 768 -w 1024 -windowed`

### Launch Borderless Now
Launches with:

- `-noborder -window`

### Set mat_queue_mode = 2 / -1
Updates `config.cfg` and writes a timestamped backup before changes.

### Reset CFG
Replaces the user `config.cfg` with the configured template and creates a timestamped backup of the previous config first.

### Reset Registry Key
Deletes:

- `HKEY_CURRENT_USER\Software\Valve\Source\iosoccer`

Requires two explicit confirmations.

### Delete Game Folder
Deletes the install folder only when it passes a strict path safety check (`...\steamapps\common\IOSoccer`) and after typed confirmation.

## Safety

- Destructive actions require confirmation.
- `config.cfg` writes are backup-first.
- Registry delete is scoped to IOSoccer key only.
- Folder delete is blocked if path looks unsafe.

## Troubleshooting

### Steam or App ID is not detected

- Click `Scan Steam`
- If still missing, enter App ID manually when prompted
- Or choose IOSoccer install folder manually for config/folder actions

### Template config source path is unavailable

The app falls back to an embedded template so the reset action still works.

## License

MIT - see [LICENSE](LICENSE)
