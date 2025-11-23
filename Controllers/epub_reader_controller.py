from ebooklib import epub, ITEM_DOCUMENT
from PIL import Image, ImageDraw, ImageFont
from Views.epub_reader_view import EpubReaderView
from bs4 import BeautifulSoup

class EpubReaderController:
    def __init__(self, display, book_path):
        self.display = display
        self.book = epub.read_epub(book_path)
        self.view = EpubReaderView(display)
        self.pages = self._extract_pages()
        self.current_page = 0

    def _extract_pages(self):
        # Simple text extraction, one page per item
        pages = []
        for item in self.book.get_items_of_type(ITEM_DOCUMENT):
            text = item.get_content().decode("utf-8", errors="ignore")
            img = self._render_text_to_image(text)
            pages.append(img)
        return pages if pages else [self._render_text_to_image("No content")]

    def _render_text_to_image(self, html):
        img = Image.new("1", (self.display.width, self.display.height), 255)
        draw = ImageDraw.Draw(img)
        soup = BeautifulSoup(html, "html.parser")

        font_normal = self.display.font_title
        font_heading = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_subheading = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)

        x, y = 20, 20
        line_spacing = 8

        for elem in soup.body.find_all(["h1", "h2", "h3", "p"], recursive=True):
            text = elem.get_text()
            if elem.name == "h1":
                draw.text((x, y), text, font=font_heading, fill=0)
                bbox = draw.textbbox((x, y), text, font=font_heading)
                h = bbox[3] - bbox[1]
                y += h + line_spacing * 2
            elif elem.name == "h2":
                draw.text((x, y), text, font=font_subheading, fill=0)
                bbox = draw.textbbox((x, y), text, font=font_subheading)
                h = bbox[3] - bbox[1]
                y += h + line_spacing * 2
            elif elem.name == "h3":
                draw.text((x, y), text, font=font_subheading, fill=0)
                bbox = draw.textbbox((x, y), text, font=font_subheading)
                h = bbox[3] - bbox[1]
                y += h + line_spacing
            elif elem.name == "p":
                max_width = self.display.width - 40
                lines = []
                words = text.split()
                line = ""
                for word in words:
                    test_line = line + " " + word if line else word
                    bbox = draw.textbbox((x, y), test_line, font=font_normal)
                    w = bbox[2] - bbox[0]
                    if w > max_width:
                        lines.append(line)
                        line = word
                    else:
                        line = test_line
                if line:
                    lines.append(line)
                for l in lines:
                    draw.text((x, y), l, font=font_normal, fill=0)
                    bbox = draw.textbbox((x, y), l, font=font_normal)
                    h = bbox[3] - bbox[1]
                    y += h + line_spacing
                y += line_spacing

            if y > self.display.height - 40:
                break

        return img

    def show_page(self):
        self.view.display_page(self.pages[self.current_page])

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.show_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()

    def _find_toc_item(self):
        # Find the item containing the TOC (usually named 'toc' or 'index')
        for item in self.book.get_items_of_type(ITEM_DOCUMENT):
            if "toc" in item.get_name().lower() or "index" in item.get_name().lower():
                return item
        return None

    def get_toc(self):
        toc_item = self._find_toc_item()
        if not toc_item:
            return []
        soup = BeautifulSoup(toc_item.get_content(), "html.parser")
        toc_links = []
        for a in soup.select("nav[epub\\:type='toc'] a"):
            toc_links.append({
                "title": a.text.strip(),
                "href": a.get("href")
            })
        return toc_links

    def show_toc(self):
        self.toc = self.get_toc()
        self.toc_selected_index = 0
        self._render_toc()

    def _render_toc(self):
        self.display.clear_framebuffer()
        y = 10
        for i, entry in enumerate(self.toc):
            selected = (i == self.toc_selected_index)
            # Draw radio button
            radio_x = 20
            radio_y = y + 12
            radio_radius = 10
            self.display.draw.ellipse(
                [(radio_x - radio_radius, radio_y - radio_radius),
                 (radio_x + radio_radius, radio_y + radio_radius)],
                outline=0, width=2
            )
            if selected:
                self.display.draw.ellipse(
                    [(radio_x - radio_radius//2, radio_y - radio_radius//2),
                     (radio_x + radio_radius//2, radio_y + radio_radius//2)],
                    fill=0
                )
            # Draw title
            self.display.draw.text((radio_x + 2 * radio_radius + 8, y), entry["title"], fill=0)
            y += 32
        self.display.update_display()

    def toc_next(self):
        if self.toc_selected_index < len(self.toc) - 1:
            self.toc_selected_index += 1
            self._render_toc()

    def toc_prev(self):
        if self.toc_selected_index > 0:
            self.toc_selected_index -= 1
            self._render_toc()

    def toc_select(self):
        href = self.toc[self.toc_selected_index]["href"]
        self.jump_to_chapter(href)

    def jump_to_chapter(self, href):
        # Find the item by href and render it
        for item in self.book.get_items_of_type(ITEM_DOCUMENT):
            if item.get_name().endswith(href):
                text = item.get_content().decode("utf-8", errors="ignore")
                img = self._render_text_to_image(text)
                self.view.display_page(img)
                self.current_page = None  # Not in paged mode
                break
