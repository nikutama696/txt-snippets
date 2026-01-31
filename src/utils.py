"""OS-specific utilities for txt-snippets."""

import os
import sys
import subprocess
from pathlib import Path


def get_app_path() -> str:
    """Get the path to the main script."""
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        return sys.executable
    else:
        # Running as script
        return os.path.abspath(sys.argv[0])


def is_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == "darwin"


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


class LaunchAtLogin:
    """Manage launch at login settings."""

    PLIST_NAME = "com.user.txtsnippets.plist"

    @classmethod
    def get_launch_agents_dir(cls) -> Path:
        """Get the LaunchAgents directory path."""
        return Path.home() / "Library" / "LaunchAgents"

    @classmethod
    def get_plist_path(cls) -> Path:
        """Get the plist file path."""
        return cls.get_launch_agents_dir() / cls.PLIST_NAME

    @classmethod
    def enable_macos(cls) -> bool:
        """Enable launch at login on macOS."""
        try:
            plist_dir = cls.get_launch_agents_dir()
            plist_dir.mkdir(parents=True, exist_ok=True)

            app_path = get_app_path()
            python_path = sys.executable

            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.txtsnippets</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""
            plist_path = cls.get_plist_path()
            with open(plist_path, "w", encoding="utf-8") as f:
                f.write(plist_content)

            # Load the launch agent
            subprocess.run(["launchctl", "load", str(plist_path)], check=False)
            return True
        except Exception as e:
            print(f"Failed to enable launch at login: {e}")
            return False

    @classmethod
    def disable_macos(cls) -> bool:
        """Disable launch at login on macOS."""
        try:
            plist_path = cls.get_plist_path()
            if plist_path.exists():
                # Unload the launch agent
                subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
                plist_path.unlink()
            return True
        except Exception as e:
            print(f"Failed to disable launch at login: {e}")
            return False

    @classmethod
    def enable_windows(cls) -> bool:
        """Enable launch at login on Windows."""
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_path = get_app_path()
            python_path = sys.executable

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(
                    key,
                    "txt-snippets",
                    0,
                    winreg.REG_SZ,
                    f'"{python_path}" "{app_path}"',
                )
            return True
        except Exception as e:
            print(f"Failed to enable launch at login: {e}")
            return False

    @classmethod
    def disable_windows(cls) -> bool:
        """Disable launch at login on Windows."""
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                try:
                    winreg.DeleteValue(key, "txt-snippets")
                except FileNotFoundError:
                    pass  # Already not registered
            return True
        except Exception as e:
            print(f"Failed to disable launch at login: {e}")
            return False

    @classmethod
    def set_enabled(cls, enabled: bool) -> bool:
        """Set launch at login state."""
        if is_macos():
            return cls.enable_macos() if enabled else cls.disable_macos()
        elif is_windows():
            return cls.enable_windows() if enabled else cls.disable_windows()
        return False

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if launch at login is currently enabled."""
        if is_macos():
            return cls.get_plist_path().exists()
        elif is_windows():
            try:
                import winreg

                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ
                ) as key:
                    winreg.QueryValueEx(key, "txt-snippets")
                    return True
            except (FileNotFoundError, OSError):
                return False
        return False


def open_file_in_editor(filepath: str | Path) -> None:
    """Open a file in the system's default text editor."""
    filepath = str(filepath)
    if is_macos():
        subprocess.run(["open", filepath], check=False)
    elif is_windows():
        os.startfile(filepath)
    else:
        # Linux fallback
        subprocess.run(["xdg-open", filepath], check=False)
