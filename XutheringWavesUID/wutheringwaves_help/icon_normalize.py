"""帮助图标标准化脚本

功能：
1. 将目录下所有 GIF 转为 150x150 RGBA PNG（重名覆盖，删除 GIF）
2. 将所有非 150x150 的 PNG resize 到 150x150
3. 将非 RGBA 模式的 PNG 转为 RGBA
4. 透明区域占比 < 0.3 的图标，内容缩小 20% 居中放到透明画布上

用法：python icon_normalize.py [icon_path目录]
默认处理同目录下的 icon_path/
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

TARGET_SIZE = (150, 150)
SHRINK_THRESHOLD = 0.3  # 透明区域占比低于此值则缩小
SHRINK_FACTOR = 0.8


def normalize_icons(icon_dir: Path):
    # 1. GIF -> PNG
    for f in sorted(icon_dir.glob("*.gif")):
        out = f.with_suffix(".png")
        img = Image.open(f)
        img = img.convert("RGBA").resize(TARGET_SIZE, Image.LANCZOS)
        img.save(out)
        f.unlink()
        print(f"[GIF->PNG] {f.name} -> {out.name}")

    # 2. Resize + RGBA
    for f in sorted(icon_dir.glob("*.png")):
        img = Image.open(f)
        changed = False

        if img.mode != "RGBA":
            img = img.convert("RGBA")
            changed = True

        if img.size != TARGET_SIZE:
            img = img.resize(TARGET_SIZE, Image.LANCZOS)
            changed = True

        if changed:
            img.save(f)
            print(f"[标准化] {f.name} -> {img.mode} {TARGET_SIZE}")

    # 3. 透明区域太少的缩小内容
    for f in sorted(icon_dir.glob("*.png")):
        img = Image.open(f).convert("RGBA")
        alpha = np.array(img)[:, :, 3]
        transparent_ratio = np.sum(alpha == 0) / alpha.size

        if transparent_ratio < SHRINK_THRESHOLD:
            w, h = img.size
            new_w, new_h = int(w * SHRINK_FACTOR), int(h * SHRINK_FACTOR)
            shrunk = img.resize((new_w, new_h), Image.LANCZOS)
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            offset_x = (w - new_w) // 2
            offset_y = (h - new_h) // 2
            canvas.paste(shrunk, (offset_x, offset_y), shrunk)
            canvas.save(f)
            print(f"[缩小] 透明占比 {transparent_ratio:.2%} -> {f.name}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        target = Path(__file__).parent / "icon_path"

    if not target.is_dir():
        print(f"目录不存在: {target}")
        sys.exit(1)

    print(f"处理目录: {target}")
    normalize_icons(target)
    print("完成")
