import zipfile
from PIL import Image
from Views.cbz_reader_view import CBZReaderView

class CBZReaderController:
    def __init__(self, display, cbz_path):
        self.display = display
        self.cbz_path = cbz_path
        self.view = CBZReaderView(display)
        self.images = []
        self.current_page = 0
        self._load_images()

    def _load_images(self):
        # Only load image file names, not the images themselves
        with zipfile.ZipFile(self.cbz_path, 'r') as archive:
            self.image_files = sorted(
                [f for f in archive.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            )
        self.total_pages = len(self.image_files)

    def _get_page_image(self, index):
        # Load, resize, and convert image on demand
        with zipfile.ZipFile(self.cbz_path, 'r') as archive:
            with archive.open(self.image_files[index]) as file:
                img = Image.open(file).convert("L")
                img = img.resize((self.display.width, self.display.height))
                img = img.point(lambda x: 0 if x < 128 else 255, '1')
                return img

    def show_page(self):
        if 0 <= self.current_page < self.total_pages:
            img = self._get_page_image(self.current_page)
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