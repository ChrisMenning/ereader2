import zipfile
import threading
from PIL import Image, ImageOps, ImageEnhance
from Views.cbz_reader_view import CBZReaderView

CACHE_SIZE = 50

class CBZReaderController:
    def __init__(self, display, cbz_path):
        self.display = display
        self.cbz_path = cbz_path
        self.view = CBZReaderView(display)
        self.images = []
        self.current_page = 0
        self._load_images()
        self._page_cache = {}
        self._cache_start = 0
        self._cache_end = min(CACHE_SIZE, self.total_pages)
        self._cache_thread = None
        # Load first page synchronously
        self._page_cache[self.current_page] = self._get_page_image(self.current_page)
        # Start background cache
        self._start_cache_thread(self._cache_start, self._cache_end)

    def _load_images(self):
        with zipfile.ZipFile(self.cbz_path, 'r') as archive:
            self.image_files = sorted(
                [f for f in archive.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            )
        self.total_pages = len(self.image_files)

    def _preload_pages(self, start, end):
        for i in range(start, end):
            if 0 <= i < self.total_pages and i not in self._page_cache:
                self._page_cache[i] = self._get_page_image(i)
        # Remove pages outside the cache window
        for k in list(self._page_cache.keys()):
            if k < start or k >= end:
                del self._page_cache[k]

    def _start_cache_thread(self, start, end):
        if self._cache_thread and self._cache_thread.is_alive():
            return  # Already caching
        def cache_worker():
            self._preload_pages(start, end)
        self._cache_thread = threading.Thread(target=cache_worker, daemon=True)
        self._cache_thread.start()

    def _get_page_image(self, index):
        with zipfile.ZipFile(self.cbz_path, 'r') as archive:
            with archive.open(self.image_files[index]) as file:
                img = Image.open(file).convert("L")
                if img.width > img.height:
                    img = img.rotate(270, expand=True)
                img = ImageOps.autocontrast(img)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2.0)
                img_ratio = img.width / img.height
                disp_ratio = self.display.width / self.display.height
                if img_ratio > disp_ratio:
                    new_width = self.display.width
                    new_height = int(new_width / img_ratio)
                else:
                    new_height = self.display.height
                    new_width = int(new_height * img_ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                final_img = Image.new("L", (self.display.width, self.display.height), 255)
                paste_x = (self.display.width - new_width) // 2
                paste_y = (self.display.height - new_height) // 2
                final_img.paste(img, (paste_x, paste_y))
                return final_img

    def show_page(self):
        # Check if current page is outside cache window
        if not (self._cache_start <= self.current_page < self._cache_end):
            self._cache_start = (self.current_page // CACHE_SIZE) * CACHE_SIZE
            self._cache_end = min(self._cache_start + CACHE_SIZE, self.total_pages)
            self._start_cache_thread(self._cache_start, self._cache_end)
        # If not cached, load synchronously
        if self.current_page not in self._page_cache:
            self._page_cache[self.current_page] = self._get_page_image(self.current_page)
        img = self._page_cache[self.current_page]
        self.view.display_page(
            img,
            page_num=self.current_page,
            total_pages=self.total_pages,
            cbz_filename=self.cbz_path.split('/')[-1]
        )

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()