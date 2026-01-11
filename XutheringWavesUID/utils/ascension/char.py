import copy
import re
from typing import Union, Optional

from msgspec import json as msgjson

from gsuid_core.logger import logger

from .model import CharacterModel
from ..ascension.constant import fixed_name, sum_percentages
from ..resource.RESOURCE_PATH import MAP_DETAIL_PATH

MAP_PATH = MAP_DETAIL_PATH / "char"
char_id_data = {}
_data_loaded = False


def read_char_json_files(directory):
    global char_id_data
    files = directory.rglob("*.json")

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = msgjson.decode(f.read())
                file_name = file.name.split(".")[0]
                char_id_data[file_name] = data
        except Exception as e:
            logger.exception(f"read_char_json_files load fail decoding {file}", e)


def ensure_data_loaded(force: bool = False):
    """确保角色数据已加载

    Args:
        force: 如果为 True，强制重新加载所有数据，即使已经加载过
    """
    global _data_loaded
    if (_data_loaded and not force) or not MAP_PATH.exists():
        return
    read_char_json_files(MAP_PATH)
    _data_loaded = True


class WavesCharResult:
    def __init__(self):
        self.name = ""
        self.starLevel = 4
        self.stats = {"life": 0.0, "atk": 0.0, "def": 0.0}
        self.statsWeakness = {
            "weaknessBuildUp": 0,
            "weaknessBuildUpMax": 10000,
            "weaknessTotalBonus": 0,
            "breakWeaknessRatio": 10000,
            "weaknessMastery": 0
        },
        self.skillTrees = {}
        self.fixed_skill = {}


def get_breach(breach: Union[int, None], level: int):
    if breach is None:
        if level <= 20:
            breach = 0
        elif level <= 40:
            breach = 1
        elif level <= 50:
            breach = 2
        elif level <= 60:
            breach = 3
        elif level <= 70:
            breach = 4
        elif level <= 80:
            breach = 5
        elif level <= 90:
            breach = 6
        else:
            breach = 0

    return breach


def extract_param_index(skill_desc: str, search_pattern: str) -> int:
    """
    从技能描述中提取参数索引

    Args:
        skill_desc: 技能描述文本，如 "莫宁的共鸣效率提升{4}..."
        search_pattern: 搜索模式，如 "共鸣效率提升"

    Returns:
        参数索引，如果找不到则返回 0

    Examples:
        >>> extract_param_index("莫宁的共鸣效率提升{4}", "共鸣效率提升")
        4
        >>> extract_param_index("攻击提升15%", "攻击提升")
        0
    """
    # 在描述中查找搜索模式之后是否有 {数字} 的模式
    pattern_index = skill_desc.find(search_pattern)
    if pattern_index == -1:
        return 0

    # 从搜索模式的位置开始，查找后面的 {数字}
    rest_of_desc = skill_desc[pattern_index + len(search_pattern):pattern_index + len(search_pattern) + 20]

    # 使用正则表达式匹配 {数字}
    match = re.search(r'\{(\d+)\}', rest_of_desc)
    if match:
        try:
            return int(match.group(1))
        except (ValueError, IndexError):
            pass

    return 0


def get_char_detail(char_id: Union[str, int], level: int, breach: Union[int, None] = None) -> WavesCharResult:
    """
    breach 突破
    resonLevel 精炼
    """
    ensure_data_loaded()
    result = WavesCharResult()
    if str(char_id) not in char_id_data:
        logger.exception(f"get_char_detail char_id: {char_id} not found")
        return result

    breach = get_breach(breach, level)

    char_data = char_id_data[str(char_id)]
    result.name = char_data["name"]
    result.starLevel = char_data["starLevel"]
    result.stats = copy.deepcopy(char_data["stats"][str(breach)][str(level)])
    result.statsWeakness = copy.deepcopy(char_data["statsWeakness"])
    result.skillTrees = char_data["skillTree"]

    char_data["skillTree"].items()
    for key, value in char_data["skillTree"].items():
        skill_info = value.get("skill", {})
        name = skill_info.get("name", "")
        if name in fixed_name and breach >= 3:
            name = name.replace("提升", "").replace("全", "")
            if name not in result.fixed_skill:
                result.fixed_skill[name] = "0%"

            result.fixed_skill[name] = sum_percentages(skill_info["param"][0], result.fixed_skill[name])

        if skill_info.get("type") == "固有技能":
            for i, name in enumerate(fixed_name):
                if skill_info["desc"].startswith(name) or skill_info["desc"].startswith(f"{char_data['name']}的{name}"):
                    name = name.replace("提升", "").replace("全", "")
                    if name not in result.fixed_skill:
                        result.fixed_skill[name] = "0%"

                    # 从描述中提取参数索引
                    search_pattern = name if skill_info["desc"].startswith(name) else f"{char_data['name']}的{name}"
                    param_index = extract_param_index(skill_info["desc"], search_pattern)

                    # 尝试获取参数值
                    try:
                        param_value = skill_info["param"][param_index]
                        result.fixed_skill[name] = sum_percentages(param_value, result.fixed_skill[name])
                    except (IndexError, KeyError, TypeError) as e:
                        logger.warning(f"get_char_detail extract_param_index failed for char_id {char_id}, skill {name}: {e}")

    return result


def get_char_detail2(role) -> WavesCharResult:
    role_id = role.role.roleId
    role_level = role.role.level
    role_breach = role.role.breach
    return get_char_detail(role_id, role_level, role_breach)


def get_char_id(char_name, loose: bool = False) -> Optional[str]:
    ensure_data_loaded()
    if not loose:
        return next((_id for _id, value in char_id_data.items() if value["name"] == char_name), None)
    else:
        for _id, value in char_id_data.items():
            if char_name in value["name"] or value["name"] in char_name:
                return _id
        return None


def get_char_model(char_id: Union[str, int]) -> Optional[CharacterModel]:
    ensure_data_loaded()
    if str(char_id) not in char_id_data:
        return None
    return CharacterModel(**char_id_data[str(char_id)])
