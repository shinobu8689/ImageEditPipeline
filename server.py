import io
import os
import copy
import base64
import traceback
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from PIL import Image
from img_obj import ImgX

# ── app ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="ImageEditPipeline")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

BASE_DIR = Path(__file__).resolve().parent

# ── global state ───────────────────────────────────────────────────────────────
layer: list[ImgX] = []
def_h_scale: int = 1752
scav_flag: bool = False


# ── helpers ────────────────────────────────────────────────────────────────────
def img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def layer_info(i: int) -> dict:
    lyr = layer[i]
    return {
        "index": i,
        "name": lyr.name,
        "size": list(lyr.img.size),
        "preview": img_to_b64(lyr.img),
    }


def all_layers_info() -> list[dict]:
    return [layer_info(i) for i in range(len(layer))]


def composite_down(position: int):
    if position <= 0:
        raise ValueError(f"Cannot composite down layer {position}.")
    base = layer[position - 1]
    overlay = layer[position]
    composited = ImgX(base.name, Image.alpha_composite(base.img, overlay.img))
    layer[position - 1] = composited
    del layer[position]


def composite_all():
    while len(layer) > 1:
        composite_down(len(layer) - 1)


def fitx_route(args):
    idx = int(args[1])
    mode = args[2]
    if not scav_flag:
        shorter_side = min(layer[0].img.size)
        temp_h_scale = shorter_side if shorter_side < def_h_scale else def_h_scale
    else:
        temp_h_scale = def_h_scale

    if mode == "scale":
        msg = layer[idx].fit(None, layer[0].img.size, None, scale_only=True)
    elif mode == "std":
        msg = layer[idx].fit(int(args[3]), layer[0].img.size, temp_h_scale)
    elif mode == "crop":
        msg = layer[idx].fit(int(args[3]), layer[0].img.size, temp_h_scale, crop=True)
    else:
        raise ValueError(f"Unknown fitx mode: {mode}")
    return msg


def tile_route(args):
    idx = int(args[1])
    offset_rows = args[2].lower() == "true"
    if len(args) > 4 and args[3] is not None:
        size = (int(args[3]), int(args[4]))
    else:
        size = layer[0].img.size
    return layer[idx].tile(size, offset_rows=offset_rows)


def new_layer(name: str, size: tuple = None):
    if size is None:
        size = layer[0].img.size if layer else (512, 512)
    image = ImgX(name, Image.new("RGBA", size, (0, 0, 0, 0)))
    layer.append(image)
    return 1, len(layer) - 1, f'Created blank layer "{name}" at {size}'


def move_layer(src: int, dst: int):
    item = layer.pop(src)
    layer.insert(dst, item)
    return 1, dst, f"Moved layer {src} to {dst}"


def delete_layer(idx: int):
    name = layer[idx].name
    del layer[idx]
    return 1, None, f'Deleted layer {idx} ("{name}")'


COMMANDS = {
    "scav": lambda a: _set_scav(a),
    "alph": lambda a: layer[int(a[1])].alpha(float(a[2])),
    "fitx": lambda a: fitx_route(a),
    "copy": lambda a: _copy_layer(int(a[1]), a[2] if len(a) > 2 else None),
    "rmbg": lambda a: layer[int(a[1])].rmbg(),
    "comd": lambda a: (composite_down(int(a[1])), (1, int(a[1]) - 1, f"Composited down"))[1],
    "coma": lambda a: (composite_all(), (1, 0, "Composited all"))[1],
    "croa": lambda a: layer[int(a[1])].crop_adv(int(a[2]), int(a[3]), int(a[4]), int(a[5])),
    "cros": lambda a: layer[int(a[1])].crop_simple(int(a[2]), int(a[3]), int(a[4])),
    "croq": lambda a: layer[int(a[1])].crop_square(),
    "tile": lambda a: tile_route(a),
    "resz": lambda a: layer[int(a[1])].resize((int(a[2]), int(a[3]))),
    "resl": lambda a: layer[int(a[1])].rescale(float(a[2])),
    "nois": lambda a: layer[int(a[1])].add_noise(float(a[2]), a[3] if len(a) > 3 else "gaussian"),
    "movx": lambda a: layer[int(a[1])].movx(int(a[2]), int(a[3])),
    "jitt": lambda a: layer[int(a[1])].jitter_shift(int(a[2])),
    "text": lambda a: layer[int(a[1])].add_text(
        int(a[2]), int(a[3]), a[4],
        int(a[5]) if len(a) > 5 else 16,
        padding=len(a) > 6 and a[6].lower() == "true",
        font=a[7] if len(a) > 7 else "./Fonts/arial.ttf",
    ),
    "rota": lambda a: layer[int(a[1])].rotate(float(a[2])),
    "newx": lambda a: new_layer(a[1], (int(a[2]), int(a[3])) if len(a) > 3 else None),
    "movl": lambda a: move_layer(int(a[1]), int(a[2])),
    "dell": lambda a: delete_layer(int(a[1])),
}


def _set_scav(a):
    global def_h_scale, scav_flag
    def_h_scale = int(a[1])
    scav_flag = True
    return 1, None, f"Set default scale to {def_h_scale}"


def _copy_layer(L: int, name: Optional[str]):
    image = copy.deepcopy(layer[L])
    if name is None:
        name = f"{layer[L].name}_copy"
    image.name = name
    layer.append(image)
    return 1, len(layer) - 1, f'Copied layer {L} as "{name}"'


# ── routes ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = BASE_DIR / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image and push it onto the layer stack."""
    data = await file.read()
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    name = Path(file.filename).stem
    layer.append(ImgX(name, img))
    return {"layers": all_layers_info()}


@app.get("/layers")
async def get_layers():
    return {"layers": all_layers_info()}


@app.delete("/layers")
async def clear_layers():
    layer.clear()
    return {"layers": []}


class CommandRequest(BaseModel):
    command: str  # e.g. "alph 0 0.5"


@app.post("/command")
async def run_command(req: CommandRequest):
    """Execute a single DSL command string."""
    line = req.command.strip()
    if not line or line.startswith("#"):
        return {"layers": all_layers_info(), "message": "skipped"}

    args = line.split()
    cmd = args[0].lower()
    args[0] = cmd

    handler = COMMANDS.get(cmd)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown command: {cmd}")

    try:
        result = handler(args)
        message = result[2] if isinstance(result, tuple) and len(result) >= 3 else str(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{cmd} failed: {e}\n{traceback.format_exc()}")

    return {"layers": all_layers_info(), "message": message}


class WorkflowRequest(BaseModel):
    workflow: str  # multi-line DSL


@app.post("/workflow")
async def run_workflow(req: WorkflowRequest):
    """Run a full multi-line workflow on current layers."""
    log = []
    for line in req.workflow.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        args = line.split()
        cmd = args[0].lower()
        args[0] = cmd
        handler = COMMANDS.get(cmd)
        if not handler:
            log.append(f"SKIP unknown: {cmd}")
            continue
        try:
            result = handler(args)
            msg = result[2] if isinstance(result, tuple) and len(result) >= 3 else str(result)
            log.append(f"✓ {line}  →  {msg}")
        except Exception as e:
            log.append(f"✗ {line}  →  {e}")

    return {"layers": all_layers_info(), "log": log}


@app.get("/layer/{idx}/preview")
async def layer_preview(idx: int):
    if idx < 0 or idx >= len(layer):
        raise HTTPException(status_code=404, detail="Layer not found")
    return {"preview": img_to_b64(layer[idx].img), "size": list(layer[idx].img.size)}


@app.post("/layer/{idx}/save")
async def save_layer(idx: int, fmt: str = "png"):
    """Return the layer as a downloadable file (base64)."""
    if idx < 0 or idx >= len(layer):
        raise HTTPException(status_code=404, detail="Layer not found")
    lyr = layer[idx]
    buf = io.BytesIO()
    if fmt == "jpg":
        lyr.img.convert("RGB").save(buf, format="JPEG", quality=95)
        mime = "image/jpeg"
        ext = "jpg"
    else:
        lyr.img.save(buf, format="PNG")
        mime = "image/png"
        ext = "png"
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {"data": f"data:{mime};base64,{b64}", "filename": f"{lyr.name}.{ext}"}


class RenameRequest(BaseModel):
    name: str


@app.patch("/layer/{idx}/rename")
async def rename_layer(idx: int, req: RenameRequest):
    if idx < 0 or idx >= len(layer):
        raise HTTPException(status_code=404, detail="Layer not found")
    layer[idx].name = req.name
    return {"layers": all_layers_info()}


# ── filesystem browsing ────────────────────────────────────────────────────────

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}

WATCHED_FOLDERS = {
    "img":      BASE_DIR / "img",
    "material": BASE_DIR / "material",
    "output":   BASE_DIR / "output",
}


@app.get("/fs/list")
async def fs_list():
    """Return the contents of img/, material/, output/ as a tree."""
    result = {}
    for label, folder in WATCHED_FOLDERS.items():
        folder.mkdir(parents=True, exist_ok=True)
        files = []
        for f in sorted(folder.iterdir()):
            if f.is_file() and f.suffix.lower() in IMG_EXTS:
                files.append({
                    "name": f.name,
                    "path": str(f.relative_to(BASE_DIR)).replace("\\", "/"),
                    "size": f.stat().st_size,
                })
        result[label] = files
    return result


class LoadFileRequest(BaseModel):
    path: str   # relative path from BASE_DIR, e.g. "img/foo.jpg"
    name: Optional[str] = None


@app.get("/fs/thumb")
async def fs_thumb(path: str):
    """Return a small base64 thumbnail for a file-browser preview."""
    from fastapi.responses import Response
    target = (BASE_DIR / path).resolve()
    if not str(target).startswith(str(BASE_DIR)) or not target.exists():
        raise HTTPException(status_code=404, detail="Not found")
    img = Image.open(target).convert("RGBA")
    img.thumbnail((64, 64), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/fs/load")
async def fs_load(req: LoadFileRequest):
    """Load an on-disk image onto the layer stack."""
    target = (BASE_DIR / req.path).resolve()
    # Safety: must stay inside BASE_DIR
    if not str(target).startswith(str(BASE_DIR)):
        raise HTTPException(status_code=403, detail="Path outside project directory")
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {req.path}")
    img = Image.open(target).convert("RGBA")
    name = req.name or target.stem
    layer.append(ImgX(name, img))
    return {"layers": all_layers_info(), "message": f"Loaded {target.name} as layer {len(layer)-1}"}
