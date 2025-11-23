import os
import sys
import time
from PIL import Image
import io
from ebooklib import epub

from Configs.rotary_encoder_input import CLK, DT, SW, GPIO, setup_encoder
from Configs.epaper_display_output import EPaperDisplay
from Views.library_view import LibraryView

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
    """
    Returns list of dicts:
    {
        "filename": str,
        "path": str,
        "title": str,
        "thumbnail": PIL.Image
    }
    """
    books = []

    for filename in os.listdir(EBOOKS_DIR):
        full = os.path.join(EBOOKS_DIR, filename)

        if not os.path.isfile(full):
            continue
        if not filename.lower().endswith(".epub"):
            continue

        try:
            book = epub.read_epub(full)
        except:
            # Skip damaged or unsupported EPUBs
            continue

        # Title from metadata
        title = None
        if "title" in book.metadata.get("DC", {}):
            title = book.metadata["DC"]["title"][0]
        if not title:
            title = os.path.splitext(filename)[0]

        # Cover image
        cover = extract_cover(book)
        if cover:
            try:
                cover = cover.resize((THUMB_SIZE, THUMB_SIZE)).convert("1")
            except:
                cover = Image.new("1", (THUMB_SIZE, THUMB_SIZE), 255)
        else:
            # White placeholder
            cover = Image.new("1", (THUMB_SIZE, THUMB_SIZE), 255)

        books.append({
            "filename": filename,
            "path": full,
            "title": title,
            "thumbnail": cover
        })

    return books


def main():
    setup_encoder()
    display = EPaperDisplay()
    library_view = LibraryView(display)

    ebooks = get_ebooks_list()
    selected_index = 0
    prev_selected_index = None
    last_clk_state = GPIO.input(CLK)

    def render_library_view():
        library_view.display_library(ebooks, selected_index)

    render_library_view()

    try:
        while True:
            clk_state = GPIO.input(CLK)
            dt_state = GPIO.input(DT)

            if clk_state != last_clk_state:
                prev_selected_index = selected_index
                if dt_state != clk_state:
                    selected_index = (selected_index + 1) % len(ebooks) if ebooks else 0
                else:
                    selected_index = (selected_index - 1) % len(ebooks) if ebooks else 0

                library_view.display_library(ebooks, selected_index)

            last_clk_state = clk_state
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Exiting Tome Reader...")

    finally:
        display.clear()
        display.sleep()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
