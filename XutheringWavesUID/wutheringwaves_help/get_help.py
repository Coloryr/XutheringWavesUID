import json
from typing import Dict
from pathlib import Path

from PIL import Image

from gsuid_core.help.model import PluginHelp
from gsuid_core.help.draw_new_plugin_help import get_new_help

from ..version import XutheringWavesUID_version
from ..utils.image import get_footer
from ..wutheringwaves_config import PREFIX, WutheringWavesConfig

ICON = Path(__file__).parent.parent.parent / "ICON.png"
HELP_DATA = Path(__file__).parent / "help.json"
ICON_PATH = Path(__file__).parent / "icon_path"
TEXT_PATH = Path(__file__).parent / "texture2d"

HELP_DATA_NO_SIGN = Path(__file__).parent / "help_no_sign.json"

if not HELP_DATA_NO_SIGN.exists():
    with open(HELP_DATA, "r", encoding="utf-8") as f:
        help_content = json.load(f)
        help_content["个人服务"]["data"] = help_content["个人服务"]["data"][2:]
        help_content["bot主人功能"]["data"] = help_content["bot主人功能"]["data"][2:]
    with open(HELP_DATA_NO_SIGN, "w", encoding="utf-8") as f:
        json.dump(help_content, f, ensure_ascii=False, indent=4)

if not WutheringWavesConfig.get_config("HelpShowSign").data:
    HELP_DATA = HELP_DATA_NO_SIGN


def get_help_data() -> Dict[str, PluginHelp]:
    # 读取文件内容
    with open(HELP_DATA, "r", encoding="utf-8") as file:
        return json.load(file)


plugin_help = get_help_data()


async def get_help(pm: int):
    return await get_new_help(
        plugin_name="XutheringWavesUID",
        plugin_info={f"v{XutheringWavesUID_version}": ""},
        plugin_icon=Image.open(ICON),
        plugin_help=plugin_help,
        plugin_prefix=PREFIX,
        help_mode="dark",
        banner_bg=Image.open(TEXT_PATH / "banner_bg.jpg"),
        banner_sub_text="漂泊者，欢迎在这个时代醒来。",
        help_bg=Image.open(TEXT_PATH / "bg.jpg"),
        cag_bg=Image.open(TEXT_PATH / "cag_bg.png"),
        item_bg=Image.open(TEXT_PATH / "item.png"),
        icon_path=ICON_PATH,
        footer=get_footer(),
        enable_cache=False,
        column=5,
        pm=pm,
    )
