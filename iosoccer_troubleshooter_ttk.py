import os
import re
import shutil
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from typing import List, Optional, Tuple
from urllib.parse import quote
import winreg

import ttkbootstrap as tb
from ttkbootstrap.widgets.scrolled import ScrolledText

APP_TITLE = "IOSoccer Troubleshooter"
REGISTRY_DISPLAY_PATH = r"Computer\\HKEY_CURRENT_USER\\Software\\Valve\\Source\\iosoccer"
REGISTRY_SUBKEY_PATH = r"Software\\Valve\\Source\\iosoccer"
COMMON_SAFE_PARAMS = "-h 768 -w 1024 -windowed"
BORDERLESS_PARAMS = "-noborder -window"
CFG_TEMPLATE_SOURCE_PATH = r"D:\SteamLibrary\steamapps\common\IOSoccer\iosoccer\cfg\config.cfg"
CFG_TEMPLATE_CONTENT = """cfgver "1"
unbindall
bind "0" "slot0"
bind "1" "slot1"
bind "2" "slot2"
bind "3" "slot3"
bind "4" "slot4"
bind "5" "slot5"
bind "6" "slot6"
bind "7" "slot7"
bind "8" "slot8"
bind "9" "slot9"
bind "a" "+moveleft"
bind "b" "headtrack_reset_home_pos"
bind "c" "+walk"
bind "d" "+moveright"
bind "e" "+gesture"
bind "g" "+zoom"
bind "i" "say_spec"
bind "k" "+voicerecord"
bind "l" "togglejoinmenu"
bind "n" "togglecaptaincy"
bind "p" "togglewarmupmenu"
bind "q" "createplayerball"
bind "r" "shootplayerball"
bind "s" "+back"
bind "u" "say_team"
bind "v" "hud_names_toggle"
bind "w" "+forward"
bind "y" "say"
bind "`" "toggleconsole"
bind "SPACE" "+jump"
bind "TAB" "+showscores"
bind "ESCAPE" "cancelselect"
bind "SHIFT" "+speed"
bind "ALT" "+duck"
bind "CTRL" "+skill"
bind "F3" "askconnect_accept"
bind "F5" "jpeg"
bind "F9" "vr_toggle"
bind "MOUSE1" "+attack"
bind "MOUSE2" "+attack2"
bind "MWHEELUP" "cl_spec_cam_decrease_dist"
bind "MWHEELDOWN" "cl_spec_cam_increase_dist"
cl_interp_ratio "1"
r_lightmap_bicubic_set "1"
cl_chatfilter_version "1"
m_rawinput_onetime_reset "1"
playername "unnamed"
cl_matchmaking_menu "0"
mat_software_aa_strength "0.000000"
mat_software_aa_strength_vgui "1.000000"
sv_skyname "sky_day01_09_hdr"
name "SyRoX"
sv_unlockedchapters "3"
cl_logofile "materials/vgui/logos/spray.vtf"
con_enable "1"
sv_logbans "1"
rate "100000"
cl_cmdrate "100"
cl_updaterate "100"
"""
APP_BG = "#0B1220"
SIDEBAR_BG = "#0F172A"
CARD_BG = "#111827"
BORDER_COLOR = "#223047"
TEXT_PRIMARY = "#E5E7EB"
TEXT_MUTED = "#94A3B8"
TEXT_ACCENT = "#7DD3FC"


@dataclass
class HelpSection:
    title: str
    body: List[str]


@dataclass
class SteamDiscovery:
    steam_path: Optional[str] = None
    app_id: Optional[str] = None
    install_dir: Optional[str] = None
    manifest_path: Optional[str] = None


SECTIONS = [
    HelpSection(
        title="Game not starting / crashing / behaving strangely",
        body=[
            "Use the action buttons above this guide to run fixes directly.",
            "Open Sound Settings and make sure your output device is enabled.",
            "Run game in safe launch mode: -h 768 -w 1024 -windowed.",
            "Verify game files in Steam.",
            f"Delete registry key if needed: {REGISTRY_DISPLAY_PATH}",
            "Open uninstall/reinstall actions, and optionally delete game folder for clean reinstall.",
            "Open Windows Update to install latest updates and drivers.",
        ],
    ),
    HelpSection(
        title="I have problems with alt-tabbing",
        body=[
            "Use the 'Open Focus Assist' action and set game focus assist behavior to Off.",
            "If you changed mat_queue_mode to 2, use 'Set mat_queue_mode = -1' before alt-tabbing in fullscreen.",
        ],
    ),
    HelpSection(
        title="How can I use borderless windowed mode?",
        body=[
            "Use the 'Launch Borderless Now' action for -noborder -window.",
        ],
    ),
    HelpSection(
        title="What other launch parameters are there?",
        body=[
            "Common options:",
            "-h 768 -w 1024",
            "-windowed",
            "-noborder -window",
            "-width <x> -height <y>",
        ],
    ),
    HelpSection(
        title="I have a low framerate",
        body=[
            "Use 'Set mat_queue_mode = 2' to update config automatically.",
            "Warning: fullscreen alt-tab can crash with mat_queue_mode 2.",
            "Use borderless mode or revert with 'Set mat_queue_mode = -1'.",
        ],
    ),
    HelpSection(
        title="My resolution isn't in the drop-down list",
        body=[
            "Use 'Launch Safe Mode Now' first.",
            "You can also start with custom launch parameters from Steam.",
        ],
    ),
    HelpSection(
        title="My config keeps resetting",
        body=[
            "Avoid non-ASCII names in player settings due to Source SDK 2007 limitations.",
        ],
    ),
]


class IOSoccerTroubleshooter:
    def __init__(self) -> None:
        self.root = tb.Window(themename="cyborg")
        self.root.title(APP_TITLE)
        self.root.geometry("1240x780")
        self.root.minsize(1040, 700)
        self.root.configure(bg="#0A101A")

        self.discovery = SteamDiscovery()
        self._section_buttons: List[tb.Button] = []

        self._build_layout()
        self._show_section(0)
        self.root.after(120, self._scan_steam)

    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self.root, bg="#11192A", width=340)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.main = tk.Frame(self.root, bg="#0A101A")
        self.main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(3, weight=1)

        self._build_sidebar()
        self._build_main_panel()

    def _build_sidebar(self) -> None:
        top = tk.Frame(self.sidebar, bg="#11192A")
        top.pack(fill="x", padx=24, pady=(24, 8))

        tk.Label(
            top,
            text="IOSoccer",
            bg="#11192A",
            fg="#EAF4FF",
            font=("Segoe UI Semibold", 31),
        ).pack(anchor="w")

        tk.Label(
            top,
            text="Troubleshooter",
            bg="#11192A",
            fg="#67D5FF",
            font=("Segoe UI", 21, "bold"),
        ).pack(anchor="w")

        tk.Label(
            self.sidebar,
            text="Automated repair actions with safe confirmations.",
            bg="#11192A",
            fg="#9FB0C9",
            justify="left",
            wraplength=285,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=24, pady=(2, 14))

        nav_container = tk.Frame(self.sidebar, bg="#11192A")
        nav_container.pack(fill="x", padx=16)

        for idx, section in enumerate(SECTIONS):
            button = tb.Button(
                nav_container,
                text=section.title,
                bootstyle="dark-outline",
                width=34,
                cursor="hand2",
                command=lambda i=idx: self._show_section(i),
            )
            button.pack(fill="x", pady=4)
            self._section_buttons.append(button)

        spacer = tk.Frame(self.sidebar, bg="#11192A")
        spacer.pack(fill="both", expand=True)

        danger = tk.Frame(self.sidebar, bg="#1B2A44", highlightthickness=1, highlightbackground="#31476B")
        danger.pack(fill="x", padx=20, pady=(8, 20))

        tk.Label(
            danger,
            text="Danger Zone",
            bg="#1B2A44",
            fg="#F4F8FF",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 2))

        tk.Label(
            danger,
            text="Deletes IOSoccer registry settings only after 2 confirmations.",
            bg="#1B2A44",
            fg="#BFD1EA",
            justify="left",
            wraplength=280,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=12)

        tb.Button(
            danger,
            text="Reset Registry Key",
            bootstyle="danger",
            cursor="hand2",
            command=self._prompt_registry_reset,
        ).pack(fill="x", padx=12, pady=(10, 12))

    def _build_main_panel(self) -> None:
        hero = tk.Frame(self.main, bg="#121D30", highlightthickness=1, highlightbackground="#2A405F")
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self.title_label = tk.Label(
            hero,
            text="",
            bg="#121D30",
            fg="#EAF3FF",
            font=("Segoe UI Semibold", 25),
            justify="left",
            wraplength=780,
        )
        self.title_label.pack(anchor="w", padx=20, pady=(14, 4))

        tk.Label(
            hero,
            text="Use actions below to run repairs directly, then follow section notes if needed.",
            bg="#121D30",
            fg="#9FB8D6",
            font=("Segoe UI", 11),
            justify="left",
            wraplength=820,
        ).pack(anchor="w", padx=20, pady=(0, 14))

        controls = tk.Frame(self.main, bg="#0F1726", highlightthickness=1, highlightbackground="#253955")
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        controls.grid_columnconfigure(1, weight=1)

        status_box = tk.Frame(controls, bg="#111B2E", highlightthickness=1, highlightbackground="#2E4A70")
        status_box.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        status_box.grid_columnconfigure(1, weight=1)

        tk.Label(
            status_box,
            text="Detected Setup",
            bg="#111B2E",
            fg="#EAF3FF",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(8, 6))

        tk.Label(status_box, text="Steam:", bg="#111B2E", fg="#AFC5E3", font=("Segoe UI", 9, "bold")).grid(
            row=1, column=0, sticky="nw", padx=(10, 6), pady=2
        )
        self.steam_path_value = tk.Label(
            status_box,
            text="Scanning...",
            bg="#111B2E",
            fg="#DCEAFF",
            justify="left",
            wraplength=360,
            font=("Segoe UI", 9),
        )
        self.steam_path_value.grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(status_box, text="App ID:", bg="#111B2E", fg="#AFC5E3", font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, sticky="nw", padx=(10, 6), pady=2
        )
        self.app_id_value = tk.Label(
            status_box,
            text="Scanning...",
            bg="#111B2E",
            fg="#DCEAFF",
            justify="left",
            font=("Segoe UI", 9),
        )
        self.app_id_value.grid(row=2, column=1, sticky="w", pady=2)

        tk.Label(status_box, text="Install:", bg="#111B2E", fg="#AFC5E3", font=("Segoe UI", 9, "bold")).grid(
            row=3, column=0, sticky="nw", padx=(10, 6), pady=(2, 8)
        )
        self.install_dir_value = tk.Label(
            status_box,
            text="Scanning...",
            bg="#111B2E",
            fg="#DCEAFF",
            justify="left",
            wraplength=360,
            font=("Segoe UI", 9),
        )
        self.install_dir_value.grid(row=3, column=1, sticky="w", pady=(2, 8))

        tb.Button(
            status_box,
            text="Scan Steam",
            bootstyle="secondary",
            cursor="hand2",
            command=self._scan_steam,
            width=14,
        ).grid(row=1, column=2, rowspan=3, sticky="ns", padx=(6, 10), pady=8)

        action_box = tk.Frame(controls, bg="#111B2E", highlightthickness=1, highlightbackground="#2E4A70")
        action_box.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="nsew")

        for col in range(3):
            action_box.grid_columnconfigure(col, weight=1)

        tk.Label(
            action_box,
            text="One-Click Actions",
            bg="#111B2E",
            fg="#EAF3FF",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(8, 6))

        self._add_action_button(action_box, 1, 0, "Verify Files", "success-outline", self._verify_files)
        self._add_action_button(action_box, 1, 1, "Launch Safe Mode Now", "primary", self._launch_safe_mode)
        self._add_action_button(action_box, 1, 2, "Launch Borderless Now", "primary-outline", self._launch_borderless)

        self._add_action_button(action_box, 2, 0, "Set mat_queue_mode = 2", "warning", self._set_mat_queue_mode_high)
        self._add_action_button(action_box, 2, 1, "Set mat_queue_mode = -1", "warning-outline", self._set_mat_queue_mode_default)
        self._add_action_button(action_box, 2, 2, "Delete Game Folder", "danger-outline", self._delete_game_folder)

        self._add_action_button(action_box, 3, 0, "Open Steam Uninstall", "danger", self._open_steam_uninstall)
        self._add_action_button(action_box, 3, 1, "Open Steam Reinstall", "info", self._open_steam_reinstall)
        self._add_action_button(action_box, 3, 2, "Open Sound Settings", "secondary", self._open_sound_settings)

        self._add_action_button(action_box, 4, 0, "Open Focus Assist", "secondary-outline", self._open_focus_assist)
        self._add_action_button(action_box, 4, 1, "Open Windows Update", "secondary", self._open_windows_update)
        self._add_action_button(action_box, 4, 2, "Copy Launch Params", "info-outline", self._copy_launch_params)
        self._add_action_button(action_box, 5, 0, "Reset CFG", "warning-outline", self._reset_cfg_from_template)

        activity_card = tk.Frame(self.main, bg="#0F1726", highlightthickness=1, highlightbackground="#253955")
        activity_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        tk.Label(
            activity_card,
            text="Activity",
            bg="#0F1726",
            fg="#EAF3FF",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.activity_text = ScrolledText(
            activity_card,
            autohide=True,
            wrap="word",
            height=5,
            bootstyle="dark-round",
            font=("Consolas", 10),
            foreground="#D7E6FA",
            background="#0F1726",
        )
        self.activity_text.pack(fill="x", padx=10, pady=(0, 8))
        self.activity_text.text.configure(state="disabled")

        docs_card = tk.Frame(self.main, bg="#0F1726", highlightthickness=1, highlightbackground="#253955")
        docs_card.grid(row=3, column=0, sticky="nsew")
        docs_card.grid_columnconfigure(0, weight=1)
        docs_card.grid_rowconfigure(0, weight=1)

        self.content_text = ScrolledText(
            docs_card,
            autohide=True,
            wrap="word",
            bootstyle="dark-round",
            font=("Cascadia Mono", 11),
            foreground="#D7E6FA",
            background="#0F1726",
        )
        self.content_text.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.status_label = tk.Label(
            docs_card,
            text="",
            bg="#0F1726",
            fg="#9AB4D4",
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

        self.credit_label = tk.Label(
            docs_card,
            text="Mady by syrox",
            bg="#0F1726",
            fg="#5E6D84",
            font=("Segoe UI", 8),
            anchor="e",
        )
        self.credit_label.grid(row=2, column=0, sticky="e", padx=14, pady=(0, 8))

    def _add_action_button(self, parent: tk.Widget, row: int, col: int, text: str, bootstyle: str, command) -> None:
        tb.Button(
            parent,
            text=text,
            bootstyle=bootstyle,
            cursor="hand2",
            command=command,
        ).grid(row=row, column=col, sticky="ew", padx=5, pady=5, ipady=3)

    def _set_status(self, message: str, level: str = "info") -> None:
        colors = {
            "info": "#9AB4D4",
            "success": "#73D8A7",
            "warning": "#E7C37A",
            "error": "#F29999",
        }
        self.status_label.configure(text=message, fg=colors.get(level, "#9AB4D4"))
        self._log(message)

    def _log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        box = self.activity_text.text
        box.configure(state="normal")
        box.insert("end", f"[{stamp}] {message}\n")
        box.see("end")
        box.configure(state="disabled")

    def _show_section(self, index: int) -> None:
        for i, button in enumerate(self._section_buttons):
            button.configure(bootstyle="info" if i == index else "dark-outline")

        section = SECTIONS[index]
        self.title_label.configure(text=section.title)

        lines = []
        for n, item in enumerate(section.body, start=1):
            wrapped = textwrap.fill(item, width=102)
            lines.append(f"{n}. {wrapped}")

        content = "\n\n".join(lines)
        widget = self.content_text.text
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def _copy_launch_params(self) -> None:
        params = f"{COMMON_SAFE_PARAMS} {BORDERLESS_PARAMS}"
        self.root.clipboard_clear()
        self.root.clipboard_append(params)
        self._set_status("Copied launch parameters to clipboard.", "success")

    def _scan_steam(self) -> None:
        self.discovery = self._discover_steam_and_game()
        self._refresh_discovery_labels()

        if self.discovery.steam_path:
            if self.discovery.app_id:
                self._set_status("Steam and IOSoccer detected successfully.", "success")
            else:
                self._set_status("Steam detected but IOSoccer app manifest was not found.", "warning")
        else:
            self._set_status("Steam path not detected automatically.", "warning")

    def _refresh_discovery_labels(self) -> None:
        self.steam_path_value.configure(text=self.discovery.steam_path or "Not found")
        self.app_id_value.configure(text=self.discovery.app_id or "Not found")

        install_text = self.discovery.install_dir or "Not found"
        if self.discovery.install_dir and not os.path.isdir(self.discovery.install_dir):
            install_text = f"{self.discovery.install_dir} (missing on disk)"
        self.install_dir_value.configure(text=install_text)

    def _discover_steam_and_game(self) -> SteamDiscovery:
        steam_path = self._find_steam_path()
        result = SteamDiscovery(steam_path=steam_path)

        if not steam_path:
            return result

        libraries = self._collect_steam_libraries(steam_path)

        for library in libraries:
            appmanifest_dir = Path(library) / "steamapps"
            if not appmanifest_dir.is_dir():
                continue

            for manifest in sorted(appmanifest_dir.glob("appmanifest_*.acf")):
                text = self._read_text_file(str(manifest))
                if not text:
                    continue

                if not re.search(r'"name"\s*"iosoccer"', text, flags=re.IGNORECASE):
                    if not re.search(r'"installdir"\s*"iosoccer"', text, flags=re.IGNORECASE):
                        continue

                app_id = self._extract_vdf_value(text, "appid")
                install_dir_name = self._extract_vdf_value(text, "installdir") or "IOSoccer"

                result.app_id = app_id
                result.manifest_path = str(manifest)
                result.install_dir = os.path.join(library, "steamapps", "common", install_dir_name)
                return result

        for library in libraries:
            candidate = os.path.join(library, "steamapps", "common", "IOSoccer")
            if os.path.isdir(candidate):
                result.install_dir = candidate
                break

        return result

    def _find_steam_path(self) -> Optional[str]:
        lookups = [
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
        ]

        for root, subkey, value_name in lookups:
            try:
                with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ) as key:
                    value, value_type = winreg.QueryValueEx(key, value_name)
                    if value_type not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                        continue
                    path = os.path.expandvars(str(value)).replace("/", "\\")
                    if os.path.isdir(path):
                        return os.path.normpath(path)
            except OSError:
                continue

        return None

    def _collect_steam_libraries(self, steam_path: str) -> List[str]:
        libraries: List[str] = []
        seen = set()

        def add_path(raw_path: str) -> None:
            fixed = os.path.normpath(raw_path.replace("\\\\", "\\").replace("/", "\\"))
            key = os.path.normcase(fixed)
            if os.path.isdir(fixed) and key not in seen:
                seen.add(key)
                libraries.append(fixed)

        add_path(steam_path)

        lib_file = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        text = self._read_text_file(lib_file)
        if text:
            for path_value in re.findall(r'"path"\s*"([^"]+)"', text, flags=re.IGNORECASE):
                add_path(path_value)

        return libraries

    @staticmethod
    def _extract_vdf_value(text: str, key: str) -> Optional[str]:
        match = re.search(rf'"{re.escape(key)}"\s*"([^"]+)"', text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _read_text_file(path: str) -> str:
        if not os.path.isfile(path):
            return ""
        for encoding in ("utf-8", "utf-16", "cp1252", "latin-1"):
            try:
                with open(path, "r", encoding=encoding) as handle:
                    return handle.read()
            except UnicodeError:
                continue
            except OSError:
                return ""
        return ""

    def _ensure_app_id(self) -> Optional[str]:
        if self.discovery.app_id and self.discovery.app_id.isdigit():
            return self.discovery.app_id

        self._scan_steam()
        if self.discovery.app_id and self.discovery.app_id.isdigit():
            return self.discovery.app_id

        typed = simpledialog.askstring(
            APP_TITLE,
            "Could not auto-detect IOSoccer app ID. Enter app ID manually:",
            parent=self.root,
        )
        if typed and typed.strip().isdigit():
            self.discovery.app_id = typed.strip()
            self._refresh_discovery_labels()
            return self.discovery.app_id

        messagebox.showwarning(APP_TITLE, "App ID is required for Steam actions.", parent=self.root)
        return None

    def _ensure_install_dir(self) -> Optional[str]:
        if self.discovery.install_dir and os.path.isdir(self.discovery.install_dir):
            return self.discovery.install_dir

        self._scan_steam()
        if self.discovery.install_dir and os.path.isdir(self.discovery.install_dir):
            return self.discovery.install_dir

        selected = filedialog.askdirectory(
            title="Select IOSoccer install folder",
            mustexist=True,
            parent=self.root,
        )
        if selected:
            self.discovery.install_dir = selected
            self._refresh_discovery_labels()
            return selected

        messagebox.showwarning(APP_TITLE, "Install folder is required for this action.", parent=self.root)
        return None

    def _open_uri(self, uri: str, success_message: str) -> None:
        try:
            os.startfile(uri)
            self._set_status(success_message, "success")
        except OSError as err:
            messagebox.showerror(APP_TITLE, f"Could not open:\n{uri}\n\n{err}", parent=self.root)
            self._set_status(f"Failed to open URI: {uri}", "error")

    def _verify_files(self) -> None:
        app_id = self._ensure_app_id()
        if not app_id:
            return
        self._open_uri(f"steam://validate/{app_id}", "Requested Steam file verification.")

    def _launch_with_params(self, params: str, label: str) -> None:
        app_id = self._ensure_app_id()
        if not app_id:
            return

        encoded = quote(params, safe="-_=.")
        uri = f"steam://run/{app_id}//{encoded}"
        self._open_uri(uri, f"Launched IOSoccer with {label}.")

    def _launch_safe_mode(self) -> None:
        self._launch_with_params(COMMON_SAFE_PARAMS, "safe mode parameters")

    def _launch_borderless(self) -> None:
        self._launch_with_params(BORDERLESS_PARAMS, "borderless parameters")

    def _open_sound_settings(self) -> None:
        self._open_uri("ms-settings:sound", "Opened Sound settings.")

    def _open_focus_assist(self) -> None:
        self._open_uri("ms-settings:quiethours", "Opened Focus Assist settings.")

    def _open_windows_update(self) -> None:
        self._open_uri("ms-settings:windowsupdate", "Opened Windows Update settings.")

    def _open_steam_uninstall(self) -> None:
        app_id = self._ensure_app_id()
        if not app_id:
            return
        self._open_uri(f"steam://uninstall/{app_id}", "Opened Steam uninstall prompt.")

    def _open_steam_reinstall(self) -> None:
        app_id = self._ensure_app_id()
        if not app_id:
            return
        self._open_uri(f"steam://install/{app_id}", "Opened Steam install prompt.")

    @staticmethod
    def _registry_key_exists() -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_SUBKEY_PATH, 0, winreg.KEY_READ):
                return True
        except FileNotFoundError:
            return False

    def _delete_registry_tree(self, root: int, subkey: str) -> None:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            while True:
                try:
                    child = winreg.EnumKey(key, 0)
                    self._delete_registry_tree(root, f"{subkey}\\{child}")
                except OSError:
                    break
        winreg.DeleteKey(root, subkey)

    def _prompt_registry_reset(self) -> None:
        if not self._registry_key_exists():
            messagebox.showinfo(APP_TITLE, "Registry key not found. Nothing to delete.", parent=self.root)
            self._set_status("Registry key was already absent.", "info")
            return

        first_confirm = messagebox.askyesno(
            APP_TITLE,
            "This permanently deletes IOSoccer settings from your registry.\n\nContinue?",
            parent=self.root,
        )
        if not first_confirm:
            self._set_status("Registry reset canceled.", "warning")
            return

        typed = simpledialog.askstring(
            "Final confirmation",
            f"Target key:\n{REGISTRY_DISPLAY_PATH}\n\nType DELETE to confirm:",
            parent=self.root,
        )
        if typed is None or typed.strip().upper() != "DELETE":
            messagebox.showwarning(APP_TITLE, "Cancelled. Registry key was not deleted.", parent=self.root)
            self._set_status("Registry reset canceled by confirmation check.", "warning")
            return

        try:
            self._delete_registry_tree(winreg.HKEY_CURRENT_USER, REGISTRY_SUBKEY_PATH)
            messagebox.showinfo(APP_TITLE, "Done. IOSoccer registry key was deleted.", parent=self.root)
            self._set_status("Registry key deleted successfully.", "success")
        except FileNotFoundError:
            messagebox.showinfo(APP_TITLE, "Registry key not found. Nothing to delete.", parent=self.root)
            self._set_status("Registry key was already absent.", "info")
        except PermissionError:
            messagebox.showerror(APP_TITLE, "Permission denied while deleting the registry key.", parent=self.root)
            self._set_status("Permission denied while deleting registry key.", "error")
        except OSError as err:
            messagebox.showerror(APP_TITLE, f"Could not delete registry key.\n\n{err}", parent=self.root)
            self._set_status("Failed to delete registry key.", "error")

    def _set_mat_queue_mode_high(self) -> None:
        self._set_mat_queue_mode("2")

    def _set_mat_queue_mode_default(self) -> None:
        self._set_mat_queue_mode("-1")

    def _get_cfg_template_text(self) -> Tuple[str, str]:
        if os.path.isfile(CFG_TEMPLATE_SOURCE_PATH):
            content, _ = self._read_text_with_encoding(CFG_TEMPLATE_SOURCE_PATH)
            if content.strip():
                return content, CFG_TEMPLATE_SOURCE_PATH
        return CFG_TEMPLATE_CONTENT, "embedded template"

    def _reset_cfg_from_template(self) -> None:
        target_path = self._find_or_create_config_path()
        if not target_path:
            return

        template_text, template_origin = self._get_cfg_template_text()
        if not template_text.strip():
            messagebox.showerror(APP_TITLE, "Template config is empty. Reset aborted.", parent=self.root)
            self._set_status("CFG reset failed because template config was empty.", "error")
            return

        confirm = messagebox.askyesno(
            APP_TITLE,
            f"Reset config.cfg using template?\n\nSource: {template_origin}\nTarget: {target_path}",
            parent=self.root,
        )
        if not confirm:
            self._set_status("CFG reset canceled.", "warning")
            return

        try:
            if os.path.isfile(target_path):
                backup_path = f"{target_path}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                shutil.copy2(target_path, backup_path)
                self._log(f"Backup created: {backup_path}")
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

            normalized_text = template_text.rstrip("\r\n") + "\n"
            with open(target_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(normalized_text)

            self._set_status("config.cfg was reset successfully from template.", "success")
            self._log(f"Template source used: {template_origin}")
        except OSError as err:
            messagebox.showerror(APP_TITLE, f"Could not reset config.cfg.\n\n{err}", parent=self.root)
            self._set_status("Failed to reset config.cfg.", "error")

    def _set_mat_queue_mode(self, value: str) -> None:
        config_path = self._find_or_create_config_path()
        if not config_path:
            return

        content, encoding = self._read_text_with_encoding(config_path)
        newline = "\r\n" if "\r\n" in content else "\n"
        replacement = f'mat_queue_mode "{value}"'
        pattern = re.compile(r"^\s*mat_queue_mode\b.*$", flags=re.IGNORECASE | re.MULTILINE)

        if content:
            updated = pattern.sub(replacement, content)
            if updated == content:
                if not content.endswith(("\n", "\r")):
                    content += newline
                updated = content + replacement + newline
        else:
            updated = replacement + "\n"

        try:
            if os.path.isfile(config_path):
                backup_path = f"{config_path}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                shutil.copy2(config_path, backup_path)
                self._log(f"Backup created: {backup_path}")

            with open(config_path, "w", encoding=encoding, newline="") as handle:
                handle.write(updated)

            self._set_status(f"Updated mat_queue_mode to {value} in config.cfg.", "success")
        except OSError as err:
            messagebox.showerror(APP_TITLE, f"Could not update config file.\n\n{err}", parent=self.root)
            self._set_status("Failed to update config.cfg.", "error")

    def _find_or_create_config_path(self) -> Optional[str]:
        install_dir = self._ensure_install_dir()
        if not install_dir:
            return None

        candidates = [
            os.path.join(install_dir, "iosoccer", "cfg", "config.cfg"),
            os.path.join(install_dir, "cfg", "config.cfg"),
        ]

        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate

        for root, dirs, files in os.walk(install_dir):
            if os.path.basename(root).lower() == "cfg":
                for filename in files:
                    if filename.lower() == "config.cfg":
                        return os.path.join(root, filename)

        for candidate in candidates:
            parent = os.path.dirname(candidate)
            if os.path.isdir(parent):
                return candidate

        messagebox.showwarning(
            APP_TITLE,
            "Could not find a cfg folder automatically. Select your IOSoccer folder first.",
            parent=self.root,
        )
        self._set_status("Config path could not be resolved.", "warning")
        return None

    @staticmethod
    def _read_text_with_encoding(path: str) -> Tuple[str, str]:
        if not os.path.isfile(path):
            return "", "utf-8"

        for encoding in ("utf-8", "cp1252", "latin-1"):
            try:
                with open(path, "r", encoding=encoding) as handle:
                    return handle.read(), encoding
            except UnicodeError:
                continue
            except OSError:
                break

        return "", "utf-8"

    def _delete_game_folder(self) -> None:
        install_dir = self._ensure_install_dir()
        if not install_dir:
            return

        folder = Path(install_dir)
        if not folder.exists():
            messagebox.showinfo(APP_TITLE, "Install folder not found on disk.", parent=self.root)
            self._set_status("Install folder is missing, nothing deleted.", "warning")
            return

        lowered_parts = [part.lower() for part in folder.parts]
        safe_location = folder.name.lower() == "iosoccer" and "steamapps" in lowered_parts and "common" in lowered_parts
        if not safe_location:
            messagebox.showerror(
                APP_TITLE,
                "Safety check failed. Folder must be ...\\steamapps\\common\\IOSoccer.",
                parent=self.root,
            )
            self._set_status("Blocked deletion due to safety path check.", "error")
            return

        first_confirm = messagebox.askyesno(
            APP_TITLE,
            f"Delete this folder and all contents?\n\n{install_dir}",
            parent=self.root,
        )
        if not first_confirm:
            self._set_status("Game folder deletion canceled.", "warning")
            return

        typed = simpledialog.askstring(
            "Final confirmation",
            "Type DELETE FOLDER to permanently remove the IOSoccer install folder:",
            parent=self.root,
        )
        if typed is None or typed.strip().upper() != "DELETE FOLDER":
            messagebox.showwarning(APP_TITLE, "Cancelled. Folder was not deleted.", parent=self.root)
            self._set_status("Game folder deletion canceled by confirmation check.", "warning")
            return

        try:
            shutil.rmtree(install_dir)
            self.discovery.install_dir = None
            self._refresh_discovery_labels()
            self._set_status("IOSoccer install folder deleted.", "success")
        except OSError as err:
            messagebox.showerror(APP_TITLE, f"Could not delete folder.\n\n{err}", parent=self.root)
            self._set_status("Failed to delete install folder.", "error")

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    IOSoccerTroubleshooter().run()
