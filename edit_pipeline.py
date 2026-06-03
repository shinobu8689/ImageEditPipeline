import time

from PIL import Image
import copy
from img_obj import ImgX
import os
from pathlib import Path as FilePath

BASE_DIR = FilePath(__file__).resolve().parent

def load_text_file(path):
    file_path = BASE_DIR / path

    # Ensure parent directory exists (in case you later use subfolders)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create file if it doesn't exist
    if not file_path.exists():
        file_path.write_text("", encoding="utf-8")

    return file_path.read_text(encoding="utf-8")

layer = []
steps = 0
show_steps = True

img_path = "./img"
output_path = "./output"

def_h_scale = 1752    # standard scale size for testing
scav_flag = False     # flag to indicate if scav has been set, used to determine if fitx should use scav value as default scale

def composite_down(position, name=None):
    if position <= 0 :
        print(f"Cannot composite down layer {position}.")
        return

    base = layer[position-1]
    overlay = layer[position]

    # Composite the overlay onto the base
    composited = ImgX(base.name if name is None else name, Image.alpha_composite(base.img, overlay.img))

    # Replace the base layer with the composited result and remove the overlay layer
    layer[position-1] = composited
    del layer[position]
    return 1, position-1, f"Composited layer {position} down to layer {position-1}"


# int, str
# int (0 = img action, 1 = layer action), str (message to show)
# all layer action args[1] must be the target layer.
def show_layer(target_layer=None, msg=None):
    print(f"== Step {steps} =====================")
    for i in range(len(layer)):
        print(f"\tLayer {i}: {str(layer[i]):<40}", end="")
        if target_layer is not None and i == int(target_layer):
            print(f" <-- {msg}", end="")
        print()




def composite_all():
    while len(layer) > 1:
        composite_down(len(layer)-1)
    return 1, 0, f"Composited all layers down to layer 0"

def load_img(img_path, name):
    image = ImgX(name, Image.open(img_path).convert("RGBA"))
    layer.append(image)
    return 1, len(layer)-1, f'Loaded from {img_path}'

def copy_layer(L: int, name: str):
    image = copy.deepcopy(layer[L])
    if name is None: name = f"{layer[L].name}_copy"
    image.name = name
    layer.append(image)
    return 1, len(layer)-1, f'Copied layer {L} to {len(layer)-1} as "{name}"'


def fitx_route(args):
    idx = int(args[1])
    mode = args[2]
    msg = None

    if not scav_flag:
        shorter_side = min(layer[0].img.size)
        temp_h_scale = shorter_side if shorter_side < def_h_scale else def_h_scale
    else:
        temp_h_scale = def_h_scale

    if mode == "scale":     msg = layer[idx].fit(None, layer[0].img.size, None, scale_only=True)
    elif mode == "std":     msg = layer[idx].fit(int(args[3]), layer[0].img.size, temp_h_scale)
    elif mode == "crop":    msg = layer[idx].fit(int(args[3]), layer[0].img.size, temp_h_scale, crop=True)
    return msg

def tile_route(args):
    idx = int(args[1])
    offset_rows = args[2].lower() == "true"

    if len(args) > 4 and args[3] is not None:           # request custom tile size
        size = (int(args[3]), int(args[4]))
    else:
        size = layer[0].img.size                        # base img

    msg = layer[idx].tile(size, offset_rows=offset_rows)

    return msg

def set_def_h_scale(a):
    global def_h_scale
    def_h_scale = int(a[1])
    global scav_flag
    scav_flag = True
    return 1, None, f'Set default scale value to {def_h_scale}'

def toggle_show_steps(bool=None):
    global show_steps
    if bool is not None:
        show_steps = bool
    else:
        show_steps = not show_steps
    return 1, None, f'Set show steps to {show_steps}'

def wait_sequence():
    input("Paused. Press Enter to continue...")
    return 1, None, f''

def new_layer(name: str, size: tuple = None):
    if size is None:
        size = layer[0].img.size
    image = ImgX(name, Image.new("RGBA", size, (0, 0, 0, 0)))
    layer.append(image)
    return 1, len(layer)-1, f'Created blank layer "{name}" at {size}'

def move_layer(src: int, dst: int):
    if src == dst:
        return 1, dst, f'Layer {src} already at position {dst}'
    item = layer.pop(src)
    layer.insert(dst, item)
    return 1, dst, f'Moved layer {src} to position {dst}'

def delete_layer(idx: int):
    name = layer[idx].name
    del layer[idx]
    return 1, None, f'Deleted layer {idx} ("{name}")'

commands = {
    "scav": lambda a: set_def_h_scale(a),
    "load": lambda a: load_img(a[1], a[2]),
    "alph": lambda a: layer[int(a[1])].alpha(float(a[2])),
    "fitx": lambda a: fitx_route(a),
    "copy": lambda a: copy_layer(int(a[1]), a[2]),
    "rmbg": lambda a: layer[int(a[1])].rmbg(),
    "comd": lambda a: composite_down(int(a[1])),
    "coma": lambda a: composite_all(),
    "save": lambda a: layer[int(a[1])].save_jpg(f'{output_path}/{file_name}'),
    "show": lambda a: show_layer(),
    "step": lambda a: toggle_show_steps(a[1].lower() == "true"),
    "croa": lambda a: layer[int(a[1])].crop_adv(int(a[2]), int(a[3]), int(a[4]), int(a[5])),
    "cros": lambda a: layer[int(a[1])].crop_simple(int(a[2]), int(a[3]), int(a[4])),
    "croq": lambda a: layer[int(a[1])].crop_square(),
    "tile": lambda a: tile_route(a),
    "resz": lambda a: layer[int(a[1])].resize((int(a[2]), int(a[3]))),
    "resl": lambda a: layer[int(a[1])].rescale(float(a[2])),
    "wait": lambda a: wait_sequence(),
    "nois": lambda a: layer[int(a[1])].add_noise(float(a[2]), a[3] if len(a) > 3 else 'gaussian'),
    "movx": lambda a: layer[int(a[1])].movx(int(a[2]), int(a[3])),
    "jitt": lambda a: layer[int(a[1])].jitter_shift(int(a[2])),
    "text": lambda a: layer[int(a[1])].add_text(int(a[2]), int(a[3]), a[4], int(a[5]) if len(a) > 5 else 16, padding=len(a) > 6 and a[6].lower() == "true", font=a[7] if len(a) > 7 else "./Fonts/arial.ttf"),
    "rota": lambda a: layer[int(a[1])].rotate(float(a[2])),
    "newx": lambda a: new_layer(a[1], (int(a[2]), int(a[3])) if len(a) > 3 else None),
    "movl": lambda a: move_layer(int(a[1]), int(a[2])),
    "dell": lambda a: delete_layer(int(a[1]))
}


if __name__ == "__main__":
    print(f'from {img_path} to {output_path}')

    workflow_filename = input("Drag and Drop workflow here: ").strip()
    if workflow_filename == "":
        print("No filename entered. Exiting.")
        exit()
    if not os.path.exists(workflow_filename):
        print(f"File not found: {workflow_filename}")
        exit()

    workflow_str = load_text_file(workflow_filename).split("\n")

    start_time = time.time()

    for (root, dirs, file) in os.walk(img_path):
        for f in file:
            if (('jpg' in f) or ('png' in f)):
                
                layer = []
                steps = 0
                file_name = f.split('.')[0]
                print(f'==  PROCESSING\t{f}  ===============================')

                load_img(img_path + "/" + f, file_name)

                

                for each in workflow_str:
                    steps += 1
                    args = each.split()
                    cmd, *_ = args
                    handler = commands.get(cmd)
                    args[0] = args[0].lower()
                    if handler and not args[0].startswith('#'): 
                        msg = handler(args)
                        if show_steps:
                            action_type = msg[0]
                            # print(args)
                            # img action rtn:   int (action type), str (message to show)
                            # layer action rtn: int (action type), target_layer, str (message to show)
                            if action_type == 0:    # img action
                                show_layer(target_layer=args[1] if args[1].isdigit() else None, msg=msg[1])
                            elif action_type == 1:  # layer action
                                show_layer(target_layer=msg[1], msg=msg[2])
                    else:       
                        print(f"Command '{cmd}' is not supported yet.")


    print(f'=============================================')
    end_time = time.time()
    print(f"Total Execution Time: {end_time - start_time:.2f} seconds")
    input("Press Enter to exit...")