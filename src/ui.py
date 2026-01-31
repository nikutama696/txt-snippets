"""UI components for txt-snippets - System Tray and Settings dialogs."""

import subprocess
import sys
from pathlib import Path
from typing import Callable

import pystray
from pystray import MenuItem as Item

from .config import Config
from .icon import create_icon
from .utils import LaunchAtLogin, open_file_in_editor, is_macos


def show_native_file_dialog(title: str = "Select File") -> str | None:
    """
    Show a native file selection dialog.
    Uses osascript on macOS, tkinter on other platforms.
    """
    if is_macos():
        # Use AppleScript for file selection on macOS
        script = f'''
        tell application "System Events"
            activate
            set theFile to choose file with prompt "{title}" of type {{"txt", "public.plain-text"}}
            return POSIX path of theFile
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return None
    else:
        # Use tkinter on other platforms (Windows/Linux)
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        filepath = filedialog.askopenfilename(
            title=title,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        root.destroy()
        return filepath if filepath else None


def show_native_message(title: str, message: str, is_error: bool = False) -> None:
    """
    Show a native message dialog.
    """
    if is_macos():
        icon = "stop" if is_error else "note"
        script = f'''
        display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK" with icon {icon}
        '''
        try:
            subprocess.run(["osascript", "-e", script], timeout=30)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
    else:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        if is_error:
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)
        root.destroy()


def show_native_confirm(title: str, message: str) -> bool:
    """
    Show a native confirmation dialog.
    Returns True if user confirmed.
    """
    if is_macos():
        script = f'''
        display dialog "{message}" with title "{title}" buttons {{"Cancel", "OK"}} default button "OK"
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    else:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno(title, message)
        root.destroy()
        return result


class TrayApp:
    """System tray application."""

    def __init__(
        self,
        config: Config,
        on_reload: Callable[[], None],
        on_exit: Callable[[], None],
    ):
        self.config = config
        self.on_reload = on_reload
        self.on_exit = on_exit
        self.icon: pystray.Icon | None = None

    def _create_menu(self) -> pystray.Menu:
        """Create the tray menu."""
        return pystray.Menu(
            Item(
                "Launch at Login",
                self._toggle_launch_at_login,
                checked=lambda item: self.config.launch_at_login,
            ),
            pystray.Menu.SEPARATOR,
            Item("Open Library", self._open_library),
            Item("Set Library Path", self._set_library_path),
            Item("Reload", self._reload),
            pystray.Menu.SEPARATOR,
            Item("Exit", self._exit),
        )

    def _toggle_launch_at_login(self) -> None:
        """Toggle launch at login setting."""
        new_value = not self.config.launch_at_login
        self.config.launch_at_login = new_value
        LaunchAtLogin.set_enabled(new_value)

    def _open_library(self) -> None:
        """Open the library file in the default editor."""
        path = self.config.library_path
        if path and Path(path).exists():
            open_file_in_editor(path)
        else:
            show_native_message(
                "Error",
                "No library file set or file does not exist.",
                is_error=True,
            )

    def _set_library_path(self) -> None:
        """Open file dialog to set library path."""
        filepath = show_native_file_dialog("Select Snippet Library")
        if filepath:
            self.config.library_path = filepath
            self.on_reload()
            show_native_message(
                "Library Updated",
                f"Library set to:\n{filepath}",
            )

    def _reload(self) -> None:
        """Reload the snippet library."""
        self.on_reload()

    def _exit(self) -> None:
        """Exit the application."""
        self.on_exit()
        if self.icon:
            self.icon.stop()

    def run(self) -> None:
        """Run the system tray application."""
        icon_image = create_icon()
        self.icon = pystray.Icon(
            "txt-snippets",
            icon_image,
            "txt-snippets",
            menu=self._create_menu(),
        )
        self.icon.run()

    def stop(self) -> None:
        """Stop the tray application."""
        if self.icon:
            self.icon.stop()
