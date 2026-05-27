from PIL import Image
from rembg import new_session, remove

class ImgX:
    def __init__(self, name, img):
        self.name = name
        self.img = img

    def __str__(self):
        return f"{self.name} {self.img.size}"
    
    # set layer opacity
    def alpha(self, opacity):
        print(f'Setting {self.name} opacity to {opacity}')
        r, g, b, a = self.img.split()
        # Scale existing alpha by opacity rather than replacing it flatly
        new_alpha = a.point(lambda p: int(p * opacity))
        self.img = Image.merge("RGBA", (r, g, b, new_alpha))


    # fit image to base size
    def fit_wm(self, base_size):     # TODO: need to normalise
        print(f'{self.name} fitting to {base_size}')

        img_w, img_h = self.img.size
        base_w, base_h = base_size
        scale = base_h / img_h  # scale based on height to preserve aspect ratio

        self.img = self.img.resize((int(img_w * scale), int(img_h * scale)), Image.LANCZOS)
        self.img = self.img.crop((0, 0, base_w, base_h))

    def add_margin(self, top, right, bottom, left, color):
        width, height = self.img.size
        new_width = width + right + left
        new_height = height + top + bottom
        result = Image.new(self.img.mode, (new_width, new_height), color)
        result.paste(self.img, (left, top))
        self.img = result

    
    def _apply_position_padding(self, angle, base_w, base_h):
        img_w, img_h = self.img.size
        pad_right  = base_w - img_w
        pad_bottom = base_h - img_h
        half_h     = (base_h - img_h) // 2
        half_w     = (base_w - img_w) // 2

        margins = {
            7: (0,         pad_right, pad_bottom, 0        ),  # top-left
            8: (0,         half_w,    pad_bottom, half_w   ),  # top-centre
            9: (0,         0,         pad_bottom, pad_right),  # top-right
            4: (half_h,    pad_right, half_h,     0        ),  # middle-left
            5: (half_h,    half_w,    half_h,     half_w   ),  # centre
            6: (half_h,    0,         half_h,     pad_right),  # middle-right
            1: (pad_bottom, pad_right, 0,         0        ),  # bottom-left
            2: (pad_bottom, half_w,    0,         half_w   ),  # bottom-centre
            3: (pad_bottom, 0,         0,         pad_right),  # bottom-right
        }

        if angle not in margins:
            print(f'Invalid position angle: {angle}')
            return False

        self.add_margin(*margins[angle], (0, 0, 0, 0))
        return True


    def fit(self, angle, base_size, height_scale, crop=False, scale_only=False):
        """
        fit(angle, base_size, height_scale)              - angle: align with keypad 1-9 position then padding
        fit(angle, base_size, height_scale, crop=True)   - crop: scale to square based on height_scale ratio, pad tp canvas size, rescale, then crop
        fit(None, base_size, None, scale_only=True)      - scale_only: scale based on height to preserve aspect ratio, then crop to base_size
        """
        print(f'{self.name} fitting to {base_size} with angle {angle}{" w/ crop" if crop else ""}{" w/ scale_only" if scale_only else ""}')
        base_w, base_h = base_size

        if scale_only:
            # fit_wm: scale based on height to preserve aspect ratio, then crop
            img_w, img_h = self.img.size
            scale = base_h / img_h
            self.img = self.img.resize(
                (int(img_w * scale), int(img_h * scale)), Image.LANCZOS
            )
            self.img = self.img.crop((0, 0, base_w, base_h))
            return

        if crop:
            # fit_tag: scale to square based on height_scale ratio, pad, rescale, then crop
            scale = self.img.size[1] / height_scale
            self.img = self.img.resize(
                (int(scale * base_h), int(scale * base_h)), Image.LANCZOS
            )
        else:
            # fit_side: scale so image height matches base_h
            scale = base_h / height_scale
            self.img = self.img.resize(
                (int(scale * self.img.size[0]), int(scale * self.img.size[1])), Image.LANCZOS
            )

        if not self._apply_position_padding(angle, base_w, base_h):
            return

        if crop:
            img_w, img_h = self.img.size
            scale = base_h / img_h
            self.img = self.img.resize(
                (int(img_w * scale), int(img_h * scale)), Image.LANCZOS
            )
            self.img = self.img.crop((0, 0, base_w, base_h))


    def rmbg(self):
        print(f'Removing Background for {self.name}')

        session = new_session("birefnet-general")

        self.img = remove(
            self.img,
            session=session,
            alpha_matting=False,         # off — matting blurs hard edges
            post_process_mask=True,      # cleans up jagged mask boundaries
        )


    def save_png(self, path, quality=95):
        self.img.save(path + ".png", format="PNG", quality=quality, optimize=True)
        print(f'Saved as\t{path}.png')

    def save_jpg(self, path, quality=95):
        self.img.convert("RGB").save(path + ".jpg", format="JPEG", quality=quality, optimize=True)
        print(f'Saved as\t{path}.jpg')




        