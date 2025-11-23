# Library Controller

class LibraryController:
    def __init__(self, view, books):
        self.view = view
        self.books = books
        self.selected_index = 0

    def move_selection(self, direction):
        if direction == "next":
            self.selected_index = (self.selected_index + 1) % len(self.books)
        elif direction == "prev":
            self.selected_index = (self.selected_index - 1) % len(self.books)
        self.view.display_library(self.books, self.selected_index)