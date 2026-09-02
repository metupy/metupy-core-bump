# metupy/utils/file_watcher.py
"""File watcher untuk livereload."""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from typing import Callable, Optional, Set
import time

class FileWatcher:
    """Watches files for changes."""
    
    def __init__(self, callback: Callable, debounce_time: float = 0.5):
        self.callback = callback
        self.debounce_time = debounce_time
        self.observer = None
        self.event_handler = None
        self.watched_dirs: Set[Path] = set()
        self.last_event = 0        
    def watch(self, directory: Path, recursive: bool = True):
        """Watch directory for changes."""
        if directory.exists():
            self.watched_dirs.add(directory)
            
            if self.observer:
                self.observer.schedule(
                    self.event_handler,
                    str(directory),
                    recursive=recursive
                )
                
    def unwatch(self, directory: Path):
        """Stop watching directory."""
        if directory in self.watched_dirs:
            self.watched_dirs.remove(directory)
            
            if self.observer:
                self.observer.unschedule(str(directory))
                
    def start(self):
        """Start watching."""
        self.event_handler = FileChangeHandler(self)
        self.observer = Observer()
        
        for directory in self.watched_dirs:
            self.observer.schedule(
                self.event_handler,
                str(directory),
                recursive=True
            )
            
        self.observer.start()
        
    def stop(self):
        """Stop watching."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
    def _handle_event(self, event):
        """Handle file event."""
        if event.is_directory:
            return
            
        # Debounce
        current_time = time.time()
        if current_time - self.last_event < self.debounce_time:
            return
            
        self.last_event = current_time
        
        # Call callback
        self.callback(event)
        
class FileChangeHandler(FileSystemEventHandler):
    """Handles file system events."""
    
    def __init__(self, watcher):
        self.watcher = watcher
        
    def on_created(self, event):
        self.watcher._handle_event(event)
        
    def on_modified(self, event):
        self.watcher._handle_event(event)
        
    def on_deleted(self, event):
        self.watcher._handle_event(event)
        
    def on_moved(self, event):
        self.watcher._handle_event(event)