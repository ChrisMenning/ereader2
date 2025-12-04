from ebooklib import epub, ITEM_DOCUMENT
from PIL import Image, ImageDraw, ImageFont
from Views.epub_reader_view import EpubReaderView
from Views.Components.radio_button import draw_radio_button
from bs4 import BeautifulSoup, NavigableString, Tag

BLOCK_TAGS = ("p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre", "div", "table")
INLINE_BOLD = ("strong", "b")
INLINE_ITALIC = ("em", "i")

class EpubReaderController:
    def __init__(self, display, book_path):
        self.display = display
        self.book = epub.read_epub(book_path)
        self.view = EpubReaderView(display)
        self.current_page = 0
        self.toc = []
        self.toc_selected_index = 0
        self.pages = []
        self.current_chapter_index = 0
        self.chapter_cache = {}
        self._page_cache = {}  # {index: image}

    def _extract_pages(self):
        pages = []
        for item in self.book.get_items_of_type(ITEM_DOCUMENT):
            text = item.get_content().decode("utf-8", errors="ignore")
            imgs = self.paginate_html(text)
            pages.extend(imgs)
        return pages if pages else [self._render_text_to_image("No content")]

    def _render_text_to_image(self, html):
        # This is now only used for fallback
        img = Image.new("1", (self.display.width, self.display.height), 255)
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), html, font=self.display.font_title, fill=0)
        return img

    def paginate_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        font_normal = self.display.font_title
        font_heading = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_subheading = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        try:
            font_blockquote = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 16)
        except OSError:
            font_blockquote = font_normal  # fallback if font not found
        font_table = font_normal

        x_margin = 20
        y_margin = 20
        line_spacing = 8
        max_width = self.display.width - 2 * x_margin
        max_height = self.display.height - 2 * y_margin

        blocks = soup.find_all(BLOCK_TAGS)
        filtered = []
        for b in blocks:
            if any((ancestor.name in BLOCK_TAGS) for ancestor in b.parents if isinstance(ancestor, Tag)):
                parent = b.find_parent(BLOCK_TAGS)
                if parent and parent is not b and parent.name != "body":
                    continue
            filtered.append(b)
        if not filtered:
            body = soup.body or soup
            for child in body.children:
                if isinstance(child, Tag):
                    filtered.append(child)

        # Pagination logic
        pages = []
        lines = []
        y = y_margin

        def flush_page():
            nonlocal lines, y
            img = Image.new("1", (self.display.width, self.display.height), 255)
            draw = ImageDraw.Draw(img)
            for line in lines:
                txt, font, x, y_pos = line
                draw.text((x, y_pos), txt, font=font, fill=0)
            pages.append(img)
            lines = []
            y = y_margin

        for blk in filtered:
            block_text = blk.get_text(separator=" ", strip=True)
            if not block_text:
                continue

            # Headings
            if blk.name == "h1":
                font = font_heading
                txt = block_text
                bbox = ImageDraw.Draw(Image.new("1", (1, 1))).textbbox((0, 0), txt, font=font)
                h = bbox[3] - bbox[1]
                if y + h > max_height and lines:
                    flush_page()
                lines.append((txt, font, x_margin, y))
                y += h + line_spacing * 2

            elif blk.name in ["h2", "h3"]:
                font = font_subheading
                txt = block_text
                bbox = ImageDraw.Draw(Image.new("1", (1, 1))).textbbox((0, 0), txt, font=font)
                h = bbox[3] - bbox[1]
                if y + h > max_height and lines:
                    flush_page()
                lines.append((txt, font, x_margin, y))
                y += h + line_spacing * 2

            elif blk.name == "blockquote":
                font = font_blockquote
                txt = block_text
                bbox = ImageDraw.Draw(Image.new("1", (1, 1))).textbbox((0, 0), txt, font=font)
                h = bbox[3] - bbox[1]
                if y + h > max_height and lines:
                    flush_page()
                lines.append((txt, font, x_margin + 30, y))
                y += h + line_spacing * 2

            elif blk.name == "table":
                # Render table rows as lines
                for tr in blk.find_all("tr"):
                    row_text = " | ".join(td.get_text(separator=" ", strip=True) for td in tr.find_all("td"))
                    bbox = ImageDraw.Draw(Image.new("1", (1, 1))).textbbox((0, 0), row_text, font=font_table)
                    h = bbox[3] - bbox[1]
                    if y + h > max_height and lines:
                        flush_page()
                    lines.append((row_text, font_table, x_margin + 10, y))
                    y += h + line_spacing
                y += line_spacing

            else:
                # Paragraphs and other blocks, with word wrapping
                font = font_normal
                words = block_text.split()
                line = ""
                for word in words:
                    test_line = line + " " + word if line else word
                    bbox = ImageDraw.Draw(Image.new("1", (1, 1))).textbbox((0, 0), test_line, font=font)
                    w = bbox[2] - bbox[0]
                    if w > max_width and line:
                        bbox_line = ImageDraw.Draw(Image.new("1", (1, 1))).textbbox((0, 0), line, font=font)
                        h_line = bbox_line[3] - bbox_line[1]
                        if y + h_line > max_height and lines:
                            flush_page()
                        lines.append((line, font, x_margin, y))
                        y += h_line + line_spacing
                        line = word
                    else:
                        line = test_line
                if line:
                    bbox_line = ImageDraw.Draw(Image.new("1", (1, 1))).textbbox((0, 0), line, font=font)
                    h_line = bbox_line[3] - bbox_line[1]
                    if y + h_line > max_height and lines:
                        flush_page()
                    lines.append((line, font, x_margin, y))
                    y += h_line + line_spacing
                y += line_spacing

        if lines:
            flush_page()

        return pages

    def _preload_pages(self, index):
        for i in [index - 1, index, index + 1]:
            if 0 <= i < len(self.pages) and i not in self._page_cache:
                self._page_cache[i] = self.pages[i]
        for k in list(self._page_cache.keys()):
            if abs(k - index) > 1:
                del self._page_cache[k]

    def show_page(self):
        if self.pages and 0 <= self.current_page < len(self.pages):
            self._preload_pages(self.current_page)
            # Get book title robustly
            book_title = ""
            dc_meta = self.book.metadata.get("DC", {})
            if "title" in dc_meta and dc_meta["title"]:
                book_title = dc_meta["title"][0]
            elif hasattr(self.book, "title"):
                book_title = self.book.title
            # Try to get chapter title from the current chapter's item
            items = [item for item in self.book.get_items_of_type(ITEM_DOCUMENT)]
            chapter_title = ""
            if 0 <= self.current_chapter_index < len(items):
                soup = BeautifulSoup(items[self.current_chapter_index].get_content(), "html.parser")
                h1 = soup.find("h1")
                h2 = soup.find("h2")
                if h1 and h1.text.strip():
                    chapter_title = h1.text.strip()
                elif h2 and h2.text.strip():
                    chapter_title = h2.text.strip()
                else:
                    section = soup.find("section")
                    if section and section.get("title"):
                        chapter_title = section.get("title")
            # DO NOT calculate total book pages here
            self.view.display_page(
                self._page_cache[self.current_page],
                book_title=book_title,
                chapter_title=chapter_title,
                page_num=self.current_page,
                total_pages=len(self.pages),
                book_total_pages=None  # Pass None, disables book page count in footer
            )

    def next_page(self):
        if self.pages and self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.show_page()
        else:
            # At last page of chapter, try to advance to next chapter
            next_chapter = self._find_next_chapter()
            if next_chapter:
                print("[DEBUG] At end of chapter, advancing to next chapter.")
                text = next_chapter.get_content().decode("utf-8", errors="ignore")
                self.pages = self.paginate_html(text)
                self.current_page = 0
                self.show_page()
            else:
                print("[DEBUG] Already at last page and last chapter.")

    def prev_page(self):
        if self.pages and self.current_page > 0:
            self.current_page -= 1
            self.show_page()
        else:
            # At first page of chapter, try to go to previous chapter
            prev_chapter = self._find_prev_chapter()
            if prev_chapter:
                print("[DEBUG] At first page, returning to previous chapter.")
                text = prev_chapter.get_content().decode("utf-8", errors="ignore")
                self.pages = self.paginate_html(text)
                self.current_page = len(self.pages) - 1
                self.show_page()
            else:
                print("[DEBUG] Already at first page and first chapter.")

    def _find_next_chapter(self):
        print(f"[DEBUG] Finding next chapter from index {self.current_chapter_index}")
        items = [item for item in self.book.get_items_of_type(ITEM_DOCUMENT)]
        if self.current_chapter_index + 1 < len(items):
            self.current_chapter_index += 1
            return items[self.current_chapter_index]
        return None

    def _find_prev_chapter(self):
        print(f"[DEBUG] Finding previous chapter from index {self.current_chapter_index}")
        items = [item for item in self.book.get_items_of_type(ITEM_DOCUMENT)]
        if self.current_chapter_index > 0:
            self.current_chapter_index -= 1
            return items[self.current_chapter_index]
        return None

    def _find_toc_item(self):
        print(f"[DEBUG] Finding TOC item")
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
            radio_x = 20
            radio_y = y + 12
            radio_radius = 10
            draw_radio_button(self.display.draw, (radio_x, radio_y), radio_radius, selected)  # Use component
            self.display.draw.text((radio_x + 2 * radio_radius + 8, y), entry["title"], fill=0)
            y += 32
        self.display.update_display()

    def toc_next(self):
        if self.toc_selected_index < len(self.toc) - 1:
            self.toc_selected_index += 1
            print(f"[DEBUG] TOC selection moved to {self.toc_selected_index}")
            self._render_toc()

    def toc_prev(self):
        if self.toc_selected_index > 0:
            self.toc_selected_index -= 1
            print(f"[DEBUG] TOC selection moved to {self.toc_selected_index}")
            self._render_toc()

    def toc_select(self):
        href = self.toc[self.toc_selected_index]["href"]
        self.jump_to_chapter(href)

    def jump_to_chapter(self, href):
        items = [item for item in self.book.get_items_of_type(ITEM_DOCUMENT)]
        for idx, item in enumerate(items):
            if item.get_name().endswith(href):
                text = item.get_content().decode("utf-8", errors="ignore")
                self.pages = self.paginate_html(text)
                self.current_page = 0
                self.current_chapter_index = idx  # Set the current chapter index
                print(f"[DEBUG] Jumped to chapter: {href}, total pages: {len(self.pages)}")
                self.show_page()
                break

    def load_chapter(self, chapter_index):
        if chapter_index in self.chapter_cache:
            self.pages = self.chapter_cache[chapter_index]
        else:
            items = [item for item in self.book.get_items_of_type(ITEM_DOCUMENT)]
            chapter_item = items[chapter_index]
            text = chapter_item.get_content().decode("utf-8", errors="ignore")
            pages = self.paginate_html(text)
            self.chapter_cache[chapter_index] = pages
            self.pages = pages