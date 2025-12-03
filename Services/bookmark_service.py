import json
import os

BOOKMARK_FILE = "bookmark.json"

class BookmarkService:
    def __init__(self):
        self.bookmark = None
        self._load_bookmark()

    def _load_bookmark(self):
        if os.path.exists(BOOKMARK_FILE):
            try:
                with open(BOOKMARK_FILE, "r") as f:
                    self.bookmark = tuple(json.load(f))
            except Exception:
                self.bookmark = None

    def _save_bookmark(self):
        try:
            with open(BOOKMARK_FILE, "w") as f:
                json.dump(self.bookmark, f)
        except Exception:
            pass

    def place_bookmark(self, chapter_index, page_index):
        self.bookmark = (chapter_index, page_index)
        self._save_bookmark()

    def get_bookmark(self):
        return self.bookmark

    def has_bookmark(self):
        return self.bookmark is not None