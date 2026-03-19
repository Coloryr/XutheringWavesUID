from pathlib import Path
from typing import Dict, Optional, Set, Tuple, Union

from PIL import ImageDraw, ImageFont

FONT_ORIGIN_PATH = Path(__file__).parent / "waves_fonts.ttf"
FONT2_ORIGIN_PATH = Path(__file__).parent / "arial-unicode-ms-bold.ttf"
EMOJI_ORIGIN_PATH = Path(__file__).parent / "NotoColorEmoji.ttf"
FONT_BACK_PATH = (
    Path(__file__).parent.parent.parent / "templates" / "fonts" / "SourceHanSansCN-Regular.ttc"
)


def waves_font_origin(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_ORIGIN_PATH), size=size)


def ww_font_origin(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT2_ORIGIN_PATH), size=size)


def emoji_font_origin(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(EMOJI_ORIGIN_PATH), size=size)


def waves_font_back_origin(size: int) -> ImageFont.FreeTypeFont:
    """加载 Noto Sans CJK SC (index=2) 作为 fallback 字体"""
    return ImageFont.truetype(str(FONT_BACK_PATH), size=size, index=2)


# 构建 waves_fonts.ttf 的 cmap 集合，用于快速判断字符是否在主字体中
_waves_cmap: Set[int] = set()
try:
    from fontTools.ttLib import TTFont

    _waves_cmap = set(TTFont(str(FONT_ORIGIN_PATH)).getBestCmap().keys())
except ImportError:
    import logging

    logging.getLogger("XutheringWavesUID").warning(
        "[鸣潮] 未安装fonttools，多语言字体fallback将不可用，日韩文可能显示为方框。"
    )
    logging.getLogger("XutheringWavesUID").info(
        "[鸣潮] 安装方法 Linux/Mac: 在当前目录下执行 source .venv/bin/activate && uv pip install fonttools"
    )
    logging.getLogger("XutheringWavesUID").info(
        "[鸣潮] 安装方法 Windows: 在当前目录下执行 .venv\\Scripts\\activate; uv pip install fonttools"
    )
except Exception:
    pass

# fallback 字体缓存 (按 size 缓存)
_font_back_cache: Dict[int, ImageFont.FreeTypeFont] = {}


def _get_font_back(size: int) -> ImageFont.FreeTypeFont:
    if size not in _font_back_cache:
        _font_back_cache[size] = waves_font_back_origin(size)
    return _font_back_cache[size]


def get_fallback_font(font: ImageFont.FreeTypeFont) -> ImageFont.FreeTypeFont:
    """根据主字体的 size 获取对应的 fallback 字体"""
    return _get_font_back(font.size)


def _need_fallback(text: str) -> bool:
    """快速判断文本是否包含主字体缺失的字符"""
    for char in text:
        if ord(char) not in _waves_cmap:
            return True
    return False


def draw_text_with_fallback(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    fill=None,
    font: Optional[ImageFont.FreeTypeFont] = None,
    anchor=None,
    fallback_font: Optional[ImageFont.FreeTypeFont] = None,
    **kwargs,
) -> float:
    """分段 fallback 绘制文本，参数顺序与 PIL draw.text 一致。

    支持 anchor 参数 (lm/mm/rm 等)。
    返回绘制后的总宽度。
    """
    if not _waves_cmap or not text or not _need_fallback(text):
        draw.text(xy, text, fill=fill, font=font, anchor=anchor, **kwargs)
        return font.getlength(text) if font else 0

    if fallback_font is None:
        fallback_font = _get_font_back(font.size)

    # 构建分段: [(segment_text, segment_font), ...]
    segments = []
    seg = ""
    seg_font = font
    for char in text:
        f = font if ord(char) in _waves_cmap else fallback_font
        if f is seg_font:
            seg += char
        else:
            if seg:
                segments.append((seg, seg_font))
            seg = char
            seg_font = f
    if seg:
        segments.append((seg, seg_font))

    total_width = sum(f.getlength(s) for s, f in segments)

    # 根据 anchor 的水平分量调整起始 x
    x, y = xy
    h_anchor = (anchor or "l")[0]
    if h_anchor == "m":
        x -= total_width / 2
    elif h_anchor == "r":
        x -= total_width

    # 每段使用左对齐 anchor 绘制
    seg_anchor = "l" + (anchor or "la")[1] if anchor else None
    for seg_text, seg_f in segments:
        draw.text((x, y), seg_text, fill=fill, font=seg_f, anchor=seg_anchor, **kwargs)
        x += seg_f.getlength(seg_text)

    return total_width


waves_font_10 = waves_font_origin(10)
waves_font_12 = waves_font_origin(12)
waves_font_14 = waves_font_origin(14)
waves_font_16 = waves_font_origin(16)
waves_font_15 = waves_font_origin(15)
waves_font_18 = waves_font_origin(18)
waves_font_20 = waves_font_origin(20)
waves_font_22 = waves_font_origin(22)
waves_font_23 = waves_font_origin(23)
waves_font_24 = waves_font_origin(24)
waves_font_25 = waves_font_origin(25)
waves_font_26 = waves_font_origin(26)
waves_font_28 = waves_font_origin(28)
waves_font_30 = waves_font_origin(30)
waves_font_32 = waves_font_origin(32)
waves_font_34 = waves_font_origin(34)
waves_font_36 = waves_font_origin(36)
waves_font_38 = waves_font_origin(38)
waves_font_40 = waves_font_origin(40)
waves_font_42 = waves_font_origin(42)
waves_font_44 = waves_font_origin(44)
waves_font_50 = waves_font_origin(50)
waves_font_58 = waves_font_origin(58)
waves_font_60 = waves_font_origin(60)
waves_font_62 = waves_font_origin(62)
waves_font_70 = waves_font_origin(70)
waves_font_84 = waves_font_origin(84)

ww_font_12 = ww_font_origin(12)
ww_font_14 = ww_font_origin(14)
ww_font_16 = ww_font_origin(16)
ww_font_15 = ww_font_origin(15)
ww_font_18 = ww_font_origin(18)
ww_font_20 = ww_font_origin(20)
ww_font_22 = ww_font_origin(22)
ww_font_23 = ww_font_origin(23)
ww_font_24 = ww_font_origin(24)
ww_font_25 = ww_font_origin(25)
ww_font_26 = ww_font_origin(26)
ww_font_28 = ww_font_origin(28)
ww_font_30 = ww_font_origin(30)
ww_font_32 = ww_font_origin(32)
ww_font_34 = ww_font_origin(34)
ww_font_36 = ww_font_origin(36)
ww_font_38 = ww_font_origin(38)
ww_font_40 = ww_font_origin(40)
ww_font_42 = ww_font_origin(42)
ww_font_44 = ww_font_origin(44)
ww_font_50 = ww_font_origin(50)
ww_font_58 = ww_font_origin(58)
ww_font_60 = ww_font_origin(60)
ww_font_62 = ww_font_origin(62)
ww_font_70 = ww_font_origin(70)
ww_font_84 = ww_font_origin(84)

emoji_font = emoji_font_origin(109)
