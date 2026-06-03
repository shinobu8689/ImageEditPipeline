from PIL import Image
from rembg import new_session, remove
import sys
import random
import numpy as np
from PIL import ImageDraw, ImageFont

class ImgX:
    def __init__(self, name, img):
        self.name = name
        self.img = img

    def __str__(self):
        return f"{self.name:<20} {str(self.img.size)}"
    
    # set layer opacity
    def alpha(self, opacity):
        r, g, b, a = self.img.split()
        # Scale existing alpha by opacity rather than replacing it flatly
        new_alpha = a.point(lambda p: int(p * opacity))
        self.img = Image.merge("RGBA", (r, g, b, new_alpha))
        return 0, f'Opacity to {opacity}'


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
        base_w, base_h = base_size

        if scale_only:
            # fit_wm: scale based on height to preserve aspect ratio, then crop
            img_w, img_h = self.img.size
            scale = base_h / img_h
            self.img = self.img.resize(
                (int(img_w * scale), int(img_h * scale)), Image.LANCZOS
            )
            self.img = self.img.crop((0, 0, base_w, base_h))
            return 0, f'Fitted w/ Scale to {base_size}'

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
            return 0, f'Fitted w/ {"Standard" if not crop else "Crop"} to {base_size} with angle {angle}'

        if crop:
            img_w, img_h = self.img.size
            scale = base_h / img_h
            self.img = self.img.resize(
                (int(img_w * scale), int(img_h * scale)), Image.LANCZOS
            )
            self.img = self.img.crop((0, 0, base_w, base_h))
        
        return 0, f'Fitted w/ {"Standard" if not crop else "Crop"} to {base_size} with angle {angle}'


    def rmbg(self):
        print("⟲ Removing Background... (Might take a while....)", end="")
        session = new_session("birefnet-general")

        self.img = remove(
            self.img,
            session=session,
            alpha_matting=False,         # off — matting blurs hard edges
            post_process_mask=True,      # cleans up jagged mask boundaries
        )

        print("\033[2K\r", end="")  # Clear the line and return carriage
        return 0, f'Removed Background'

    def crop_adv(self, left, top, right, bottom):
        self.img = self.img.crop((left, top, right, bottom))
        return 0, f'Advance Cropped to ({left}, {top}, {right}, {bottom})'

    def crop_simple(self, align, width, height):
        """
        Crop image using a numpad-style position (1-9).
        7=top-left, 8=top-centre, 9=top-right
        4=mid-left,  5=centre,    6=mid-right
        1=bot-left,  2=bot-centre, 3=bot-right
        """
        img_w, img_h = self.img.size

        col = (align - 1) % 3  # 0=left, 1=centre, 2=right
        row = 2 - (align - 1) // 3  # 0=top, 1=middle, 2=bottom

        max_x = img_w - width
        max_y = img_h - height

        left = round(col / 2 * max_x)
        top  = round(row / 2 * max_y)

        self.img = self.img.crop((left, top, left + width, top + height))
        return 0, f'Simple Cropped to align={align}, size=({width}, {height})'

    def crop_square(self):
        img_w, img_h = self.img.size
        min_dim = min(img_w, img_h)
        left = (img_w - min_dim) // 2
        top = (img_h - min_dim) // 2
        self.img = self.img.crop((left, top, left + min_dim, top + min_dim))
        return 0, f'Cropped to Square'

    def tile(self, size: tuple[int, int], offset_rows: bool = False):

        canvas_w, canvas_h = size
        img_w, img_h = self.img.size
    
        canvas = Image.new(self.img.mode, size)
    
        half_w = img_w // 2
        row = 0
        y = 0
    
        while y < canvas_h:
            x_start = -half_w if (offset_rows and row % 2 == 1) else 0
            x = x_start
    
            while x < canvas_w:
                # Work out how much of the tile is actually visible on the canvas.
                src_x = max(0, -x)          # skip pixels that are left of the canvas
                src_y = max(0, -y)          # skip pixels that are above the canvas
                dst_x = max(0, x)
                dst_y = max(0, y)
    
                paste_w = min(img_w - src_x, canvas_w - dst_x)
                paste_h = min(img_h - src_y, canvas_h - dst_y)
    
                if paste_w > 0 and paste_h > 0:
                    region = self.img.crop((src_x, src_y, src_x + paste_w, src_y + paste_h))
                    canvas.paste(region, (dst_x, dst_y))
    
                x += img_w
    
            y += img_h
            row += 1
    
        self.img = canvas
        return 0, f'Tiled to {size} with{"out" if not offset_rows else ""} offset'

    def add_noise(self, strength: float, type: str = 'gaussian'):
        arr = np.array(self.img).astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4

        rgb = arr[..., :3]
        if type == 'gaussian':
            noise = np.random.normal(0, strength * 255, rgb.shape)
        elif type == 'uniform':
            noise = np.random.uniform(-strength * 255, strength * 255, rgb.shape)
        elif type == 'salt_pepper':
            noise = np.zeros(rgb.shape, dtype=np.float32)
            mask_salt   = np.random.random(rgb.shape[:2]) < strength / 2
            mask_pepper = np.random.random(rgb.shape[:2]) < strength / 2
            noise[mask_salt]   =  255
            noise[mask_pepper] = -255
        else:
            print(f'Unknown noise type: {type}')
            return 1, f'Unknown noise type: {type}'

        rgb = np.clip(rgb + noise, 0, 255).astype(np.uint8)

        if has_alpha:
            arr[..., :3] = rgb
            self.img = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        else:
            self.img = Image.fromarray(rgb, 'RGB')

        return 0, f'Added {type} noise at strength {strength}'

    def movx(self, x: int = 0, y: int = 0): # x: +ve = right, y: +ve = down 
        canvas_w, canvas_h = self.img.size
        canvas = Image.new(self.img.mode, (canvas_w, canvas_h), (0, 0, 0, 0))
        canvas.paste(self.img, (x, y))
        self.img = canvas
        return 0, f'Moved by x={x}, y={y}'

    def jitter_shift(self, r: int):
        x = random.randint(-r, r)
        y = random.randint(-r, r)
        self.movx(x, y)
        return 0, f'Jitter shifted within r={r}px (x={x}, y={y})'

    def add_text(self, x: int, y: int, text: str, size: int = 16, padding: bool = False, font: str = "./Fonts/arial.ttf"):
        pil_font = ImageFont.load_default() if font is None else ImageFont.truetype(font, size)

        draw_target = self.img.copy()
        draw = ImageDraw.Draw(draw_target)

        bbox = draw.textbbox((x, y), text, font=pil_font)
        canvas_w, canvas_h = self.img.size

        if padding:
            pad_right  = max(0, bbox[2] - canvas_w)
            pad_bottom = max(0, bbox[3] - canvas_h)
            if pad_right > 0 or pad_bottom > 0:
                self.add_margin(0, pad_right, pad_bottom, 0, (0, 0, 0, 0))
            draw_target = self.img.copy()
            draw = ImageDraw.Draw(draw_target)

        draw.text((x, y), text, font=pil_font)
        self.img = draw_target
        return 0, f'Added text "{text}" at ({x}, {y}), size={size}, padding={padding}'

    def rotate(self, degree: float):
        self.img = self.img.rotate(-degree, expand=True)
        return 0, f'Rotated by {degree}°'

    def resize(self, new_size):
        self.img = self.img.resize(new_size, Image.LANCZOS)
        return 0, f'Resized to {new_size}'
    
    def rescale(self, scale: float):
        new_size = (int(self.img.size[0] * scale), int(self.img.size[1] * scale))
        self.img = self.img.resize(new_size, Image.LANCZOS)
        return 0, f'Resized by a scale of {scale} to {new_size}'

    def save_png(self, path, quality=95):
        self.img.save(path + ".png", format="PNG", quality=quality, optimize=True)
        return 0, f'Saved as {path}.png'

    def save_jpg(self, path, quality=95):
        self.img.convert("RGB").save(path + ".jpg", format="JPEG", quality=quality, optimize=True)
        return 0, f'Saved as {path}.jpg'