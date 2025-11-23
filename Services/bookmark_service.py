# Simple bookmark service for storing a single bookmark per session

class BookmarkService:
    def __init__(self):
        self.bookmark = None

    def place_bookmark(self, chapter_index, page_index):
        self.bookmark = (chapter_index, page_index)

    def get_bookmark(self):
        return self.bookmark

    def has_bookmark(self):
        return self.bookmark is not None