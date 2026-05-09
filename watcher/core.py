import os, time, threading, fnmatch
from pathlib import Path

class FileWatcher:
    def __init__(self, path, patterns=None, debounce=1.0):
        self.path = Path(path)
        self.patterns = patterns or ['*']
        self.debounce = debounce
        self._callbacks = []
        self._running = False
        self._snapshot = {}

    def on_change(self, cb):
        self._callbacks.append(cb)
        return self

    def _scan(self):
        r = {}
        for root, _, files in os.walk(self.path):
            for f in files:
                fp = os.path.join(root, f)
                if any(fnmatch.fnmatch(f, p) for p in self.patterns):
                    r[fp] = os.path.getmtime(fp)
        return r

    def _poll(self):
        while self._running:
            new = self._scan()
            changes = []
            for fp in new:
                if fp not in self._snapshot:
                    changes.append(('created', fp))
                elif new[fp] != self._snapshot[fp]:
                    changes.append(('modified', fp))
            for fp in self._snapshot:
                if fp not in new:
                    changes.append(('deleted', fp))
            if changes:
                for cb in self._callbacks:
                    cb(changes)
            self._snapshot = new
            time.sleep(self.debounce)

    def start(self):
        self._snapshot = self._scan()
        self._running = True
        threading.Thread(target=self._poll, daemon=True).start()
        return self

    def stop(self):
        self._running = False
