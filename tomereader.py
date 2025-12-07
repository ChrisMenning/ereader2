import os
import sys
import threading
import time
from PIL import Image
import io
from ebooklib import epub, ITEM_DOCUMENT

from Configs.rotary_encoder_input import CLK, DT, SW, GPIO, setup_encoder
from Configs.epaper_display_output import EPaperDisplay
from Views.library_view import LibraryView
from Controllers.epub_reader_controller import EpubReaderController
from Views.epub_reader_view import EpubReaderView
from Views.reader_modal_view import ReaderModalView
from Services.bookmark_service import BookmarkService
from Controllers.cbz_reader_controller import CBZReaderController
from Views.cbz_reader_view import CBZReaderView
from Views.splash_screen_view import SplashScreenView

sys.path.append('/home/mcmudgeon/e-Paper/RaspberryPi_JetsonNano/python/lib')

EBOOKS_DIR = "ebooks"
THUMB_SIZE = 64


def extract_cover(book):
    """
    Extract the EPUB cover image using ebooklib.
    Returns a PIL.Image or None.
    """
    cover_item = None

    for item in book.get_items():
        # Check for image type and "cover" in name
        if hasattr(item, "media_type") and item.media_type.startswith("image/"):
            if "cover" in item.get_name().lower():
                cover_item = item
                break

    if not cover_item:
        return None

    try:
        return Image.open(io.BytesIO(cover_item.get_content()))
    except Exception:
        return None


def get_ebooks_list():
    books = []
    for filename in os.listdir(EBOOKS_DIR):
        full = os.path.join(EBOOKS_DIR, filename)
        if not os.path.isfile(full):
            continue
        ext = filename.lower().split('.')[-1]
        if ext not in ("epub", "cbz"):
            continue

        title = os.path.splitext(filename)[0]
        # Cover image for EPUB
        cover = None
        if ext == "epub":
            try:
                book = epub.read_epub(full)
                if "title" in book.metadata.get("DC", {}):
                    title = book.metadata["DC"]["title"][0]
                cover = extract_cover(book)
                if cover:
                    cover = cover.resize((THUMB_SIZE, THUMB_SIZE)).convert("L")
            except:
                cover = None
        # Cover image for CBZ (first image in archive)
        elif ext == "cbz":
            try:
                import zipfile
                with zipfile.ZipFile(full, 'r') as archive:
                    image_files = sorted([f for f in archive.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))])
                    if image_files:
                        with archive.open(image_files[0]) as file:
                            img = Image.open(file).convert("L")
                            cover = img.resize((THUMB_SIZE, THUMB_SIZE))
            except:
                cover = None
        if not cover:
            cover = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 255)

        books.append({
            "filename": filename,
            "path": full,
            "title": title,
            "thumbnail": cover,
            "type": ext
        })
    # Sort books by title (case-insensitive)
    books.sort(key=lambda b: b["title"].lower())
    return books


def main():
    setup_encoder()
    display = EPaperDisplay()
    splash_view = SplashScreenView(display)
    splash_view.show()
    time.sleep(2)  # Show splash for 2 seconds

    library_view = LibraryView(display)
    modal_view = ReaderModalView(display)
    bookmark_service = BookmarkService()

    ebooks = []
    selected_index = 0
    last_clk_state = GPIO.input(CLK)
    last_sw_state = GPIO.input(SW)
    in_reader = False
    in_toc = False
    in_modal = False
    modal_selected = 0
    reader_controller = None

    def render_library_view():
        library_view.display_library(ebooks, selected_index)

    # Load ebooks in a background thread
    def load_books():
        nonlocal ebooks
        ebooks = get_ebooks_list()
        render_library_view()

    threading.Thread(target=load_books, daemon=True).start()

    try:
        while True:
            clk_state = GPIO.input(CLK)
            dt_state = GPIO.input(DT)
            sw_state = GPIO.input(SW)

            # Modal navigation
            if in_modal:
                if clk_state == 0 and last_clk_state == 1:
                    if dt_state == 1:
                        modal_selected = (modal_selected - 1) % len(modal_view.get_options())
                    else:
                        modal_selected = (modal_selected + 1) % len(modal_view.get_options())
                    # Partial refresh for modal radio buttons
                    modal_view.partial_refresh_radio_buttons(len(modal_view.get_options()), modal_selected)
                if sw_state == 0 and last_sw_state == 1:
                    option = modal_view.get_options()[modal_selected]
                    print(f"[MODAL] Selected: {option}")
                    if option == "Place Bookmark":
                        if selected_book["type"] == "epub":
                            bookmark_service.place_bookmark(reader_controller.current_chapter_index, reader_controller.current_page)
                            print(f"[MODAL] Bookmark placed at chapter {reader_controller.current_chapter_index}, page {reader_controller.current_page}")
                        elif selected_book["type"] == "cbz":
                            bookmark_service.place_bookmark(None, reader_controller.current_page)
                            print(f"[MODAL] Bookmark placed at page {reader_controller.current_page}")
                    elif option == "Go to Bookmark" and bookmark_service.has_bookmark():
                        chapter_idx, page_idx = bookmark_service.get_bookmark()
                        if selected_book["type"] == "epub":
                            reader_controller.current_chapter_index = chapter_idx
                            reader_controller.load_chapter(chapter_idx)
                            reader_controller.current_page = page_idx
                            reader_controller.show_page()
                            print(f"[MODAL] Jumped to bookmark at chapter {chapter_idx}, page {page_idx}")
                        elif selected_book["type"] == "cbz":
                            reader_controller.current_page = page_idx
                            reader_controller.show_page()
                            print(f"[MODAL] Jumped to bookmark at page {page_idx}")
                    elif option == "Back to Library":
                        in_reader = False
                        in_toc = False
                        display.init_display()         # Ensure full update mode and clear framebuffer
                        render_library_view()          # Redraw the full library view
                        # Do NOT call display.init_display() again after this, as it would clear the library view
                        in_modal = False
                        modal_selected = 0
                        continue  # Skip the rest of the modal close logic for this case
                    # Cancel or after any action, close modal
                    in_modal = False
                    modal_selected = 0
                    if in_reader and not in_toc:
                        reader_controller.show_page()
                    # Restore full refresh mode after modal closes
                    display.init_display()
                last_clk_state = clk_state
                last_sw_state = sw_state
                time.sleep(0.01)
                continue

            # Encoder navigation (partial refresh for selection change)
            if clk_state == 0 and last_clk_state == 1:
                if not in_reader:
                    prev_index = selected_index
                    if dt_state == 1:
                        print("[ENCODER] Turned clockwise (Up/Back)")
                        selected_index = (selected_index - 1) % len(ebooks) if ebooks else 0
                    else:
                        print("[ENCODER] Turned counter-clockwise (Down/Next)")
                        selected_index = (selected_index + 1) % len(ebooks) if ebooks else 0
                    # Only update radio buttons if selection changed
                    if ebooks and selected_index != prev_index:
                        library_view.partial_refresh_radio_buttons(ebooks, selected_index)
                elif in_toc:
                    if dt_state == 1:
                        print("[ENCODER] Turned clockwise (Up/Back)")
                        reader_controller.toc_prev()
                    else:
                        print("[ENCODER] Turned counter-clockwise (Down/Next)")
                        reader_controller.toc_next()
                else:
                    if dt_state == 1:
                        print("[ENCODER] Turned clockwise (Up/Back)")
                        reader_controller.prev_page()
                    else:
                        print("[ENCODER] Turned counter-clockwise (Down/Next)")
                        reader_controller.next_page()

            # Button press to open reader or modal (full refresh before opening)
            if not in_reader and sw_state == 0 and last_sw_state == 1:
                selected_book = ebooks[selected_index]
                print("Opening book:", selected_book["title"])
                book_path = selected_book["path"]
                library_view.display_library(ebooks, selected_index)  # Full refresh

                display.init_display()  

                if selected_book["type"] == "epub":
                    reader_controller = EpubReaderController(display, book_path)
                    reader_controller.show_toc()
                    in_reader = True
                    in_toc = True
                elif selected_book["type"] == "cbz":
                    reader_controller = CBZReaderController(display, book_path)
                    reader_controller.show_page()
                    in_reader = True
                    in_toc = False
            elif in_toc and sw_state == 0 and last_sw_state == 1:
                reader_controller.toc_select()
                in_toc = False  # Exit TOC mode after selection
            elif in_reader and not in_toc and sw_state == 0 and last_sw_state == 1:
                in_modal = True
                modal_selected = 0
                modal_view.show_modal(modal_selected)

            last_clk_state = clk_state
            last_sw_state = sw_state
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Exiting Tome Reader...")
    finally:
        display.clear()
        display.sleep()
        GPIO.cleanup()


if __name__ == "__main__":
    main()

# When opening a chapter after TOC selection or navigation, use load_chapter:
# Example for jumping to chapter (update your jump_to_chapter logic):
def jump_to_chapter(self, href):
    items = [item for item in self.book.get_items_of_type(ITEM_DOCUMENT)]
    for idx, item in enumerate(items):
        if item.get_name().endswith(href):
            self.current_chapter_index = idx
            self.load_chapter(idx)
            self.current_page = 0
            print(f"[DEBUG] Jumped to chapter: {href}, total pages: {len(self.pages)}")
            self.show_page()
            break
