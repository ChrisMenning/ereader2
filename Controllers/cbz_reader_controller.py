import zipfile
from PIL import Image, ImageOps, ImageEnhance
from Views.cbz_reader_view import CBZReaderView

class CBZReaderController:
    def __init__(self, display, cbz_path):
        self.display = display
        self.cbz_path = cbz_path
        self.view = CBZReaderView(display)
        self.images = []
        self.current_page = 0
        self._load_images()
        self._page_cache = {}  # {index: image}
        self._preload_pages(self.current_page)

    def _load_images(self):
        # Only load image file names, not the images themselves
        with zipfile.ZipFile(self.cbz_path, 'r') as archive:
            self.image_files = sorted(
                [f for f in archive.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            )
        self.total_pages = len(self.image_files)

    def _preload_pages(self, index):
        # Preload previous, current, and next page images
        for i in [index - 1, index, index + 1]:
            if 0 <= i < self.total_pages and i not in self._page_cache:
                self._page_cache[i] = self._get_page_image(i)
        # Optionally, remove far-away pages from cache
        for k in list(self._page_cache.keys()):
            if abs(k - index) > 1:
                del self._page_cache[k]

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
                # Do NOT convert to 1-bit!
                return final_img

    def show_page(self):
        if 0 <= self.current_page < self.total_pages:
            self._preload_pages(self.current_page)
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