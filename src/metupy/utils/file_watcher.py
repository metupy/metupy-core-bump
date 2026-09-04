"""
File watcher for Metupy.

Watches files for changes and triggers callbacks.
Used for live reload functionality.
"""

import time
from pathlib import Path
from typing import Callable, Optional, Set

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class FileWatcher:
    """Watch files for changes."""

    def __init__(self, callback: Callable, debounce_time: float = 0.5):
        """
        Initialize FileWatcher.

        Args:
            callback: Function to call on file change.
            debounce_time: Minimum time between callbacks.
        """
        self.callback = callback
        self.debounce_time = debounce_time
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[FileSystemEventHandler] = None
        self.watched_dirs: Set[Path] = set()
        self.last_event = 0

    def watch(self, directory: Path, recursive: bool = True) -> None:
        """
        Watch directory for changes.

        Args:
            directory: Directory to watch.
            recursive: Watch subdirectories.
        """
        if directory.exists():
            self.watched_dirs.add(directory)

            if self.observer:
                self.observer.schedule(
                    self.event_handler,
                    str(directory),
                    recursive=recursive
                )

    def start(self) -> None:
        """Start watching files."""
        self.event_handler = FileChangeHandler(self)
        self.observer = Observer()

        for directory in self.watched_dirs:
            self.observer.schedule(
                self.event_handler,
                str(directory),
                recursive=True
            )

        self.observer.start()

    def stop(self) -> None:
        """Stop watching files."""
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def _handle_event(self, event) -> None:
        """
        Handle file system event.

        Args:
            event: File system event.
        """
        if event.is_directory:
            return

        current_time = time.time()
        if current_time - self.last_event < self.debounce_time:
            return

        self.last_event = current_time
        self.callback(event)


class FileChangeHandler(FileSystemEventHandler):
    """Handle file system change events."""

    def __init__(self, watcher: FileWatcher):
        """
        Initialize handler.

        Args:
            watcher: FileWatcher instance.
        """
        self.watcher = watcher

    def on_created(self, event) -> None:
        self.watcher._handle_event(event)

    def on_modified(self, event) -> None:
        self.watcher._handle_event(event)

    def on_deleted(self, event) -> None:
        self.watcher._handle_event(event)

    def on_moved(self, event) -> None:
        self.watcher._handle_event(event)