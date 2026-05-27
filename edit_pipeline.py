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

img_path = "./img"
output_path = "./output"

def_h_scale = 1752    # standard scale size for testing

def composite_down(position):
    if position <= 0 :
        print(f"Cannot composite down layer {position}.")
        return

    print(f"Compositing down layer {position} -> {position-1}")
    base = layer[position-1]
    overlay = layer[position]

    # Composite the overlay onto the base
    composited = ImgX(base.name, Image.alpha_composite(base.img, overlay.img))

    # Replace the base layer with the composited result and remove the overlay layer
    layer[position-1] = composited
    del layer[position]

def show_layer():
    print("Showing layers:")
    for each in layer:
        print(f"\tLayer {layer.index(each)}: {str(each)}")
        
def composite_all():
    while len(layer) > 1:
        composite_down(len(layer)-1)

def load_img(img_path, name):
    image = ImgX(name, Image.open(img_path).convert("RGBA"))
    layer.append(image)
    print(f'Loaded layer {layer[-1].name} {layer[-1].img.size}')

def copy_layer(L: int, name: str):
    image = copy.deepcopy(layer[L])
    if name is None: name = f"{layer[L].name}_copy"
    image.name = name
    layer.append(image)
    print(f"Copied layer {L} to layer {len(layer)-1}")


def parse_fitx(args):
    idx = int(args[1])
    mode = args[2]
    if mode == "scale":     layer[idx].fit(None, layer[0].img.size, None, scale_only=True)
    elif mode == "std":     layer[idx].fit(int(args[3]), layer[0].img.size, def_h_scale)
    elif mode == "crop":    layer[idx].fit(int(args[3]), layer[0].img.size, def_h_scale, crop=True)

commands = {
    "scal": lambda a: globals().update(def_h_scale=int(a[1])),
    "load": lambda a: load_img(a[1], a[2]),
    "alph": lambda a: layer[int(a[1])].alpha(float(a[2])),
    "fitx": lambda a: parse_fitx(a),
    "copy": lambda a: copy_layer(int(a[1]), a[2]),
    "rmbg": lambda a: layer[int(a[1])].rmbg(),
    "comd": lambda a: composite_down(int(a[1])),
    "coma": lambda a: composite_all(),
    "save": lambda a: layer[int(a[1])].save_jpg(f'{output_path}/{file_name}'),
    "show": lambda a: show_layer(),
}


if __name__ == "__main__":
    print(f'from {img_path} to {output_path}')

    workflow_filename = input("Please enter workflow filename (default: wf1.txt): ").strip()
    if workflow_filename == "":
        print("No filename entered. Exiting.")
        exit()
    if not os.path.exists(workflow_filename):
        print(f"File not found: {workflow_filename}")
        exit()

    workflow_str = load_text_file(workflow_filename).split("\n")



    for (root, dirs, file) in os.walk(img_path):
        for f in file:
            if (('jpg' in f) or ('png' in f)):
                
                layer = []
                file_name = f.split('.')[0]
                print(f'==  PROCESSING\t{f}  ===============================')

                load_img(img_path + "/" + f, "base_img")

                for each in workflow_str:
                    args = each.split()
                    cmd, *_ = args
                    handler = commands.get(cmd)
                    if handler: handler(args)
                    else:       print(f"Command '{cmd}' is not supported yet.")


    print(f'=============================================')
    input("Press Enter to exit...")
    





