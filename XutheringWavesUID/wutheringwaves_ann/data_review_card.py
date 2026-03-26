from typing import Union
from pathlib import Path
from datetime import datetime

from gsuid_core.logger import logger

from ..utils.waves_api import waves_api
from ..utils.api.model import DataReview
from ..utils.resource.RESOURCE_PATH import waves_templates
from ..utils.resource.RESOURCE_PATH import ANN_CARD_PATH
from ..utils.render_utils import (
    PLAYWRIGHT_AVAILABLE,
    get_logo_b64,
    get_footer_b64,
    image_to_base64,
    get_image_b64_with_cache,
    render_html,
)

TIME_TYPE_MAP = {
    "LING_CHEN": "凌晨",
    "ZAOCHEN": "早晨",
    "SHANG_WU": "上午",
    "ZHONG_WU": "中午",
    "XIA_WU": "下午",
    "BANG_WAN": "傍晚",
    "WAN_SHANG": "晚上",
    "SHEN_YE": "深夜",
}


def format_latest_time(time_str: str) -> str:
    try:
        dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%Y年%m月%d日%H:%M")
    except Exception:
        return time_str


async def data_review_card(token: str) -> Union[bytes, str]:
    try:
        res = await waves_api.get_data_review(token)
        if not res.success:
            return f"获取年度报告失败: {res.msg}"

        raw = res.data
        if not raw:
            return "获取年度报告失败: 数据为空"

        data = DataReview.model_validate(raw)

        if not data.page1:
            return "获取年度报告失败: 无数据"

        card_path = Path(__file__).parent / "texture2d" / "card.webp"
        card_b64 = image_to_base64(card_path)

        # 获取用户头像
        user_avatar = ""
        mine_res = await waves_api.get_user_mine_v2(token)
        if mine_res.success:
            mine_data = mine_res.data or {}
            mine_info = mine_data.get("mine", {}) if isinstance(mine_data, dict) else {}
            head_url = mine_info.get("headUrl", "")
            if head_url:
                user_avatar = await get_image_b64_with_cache(head_url, ANN_CARD_PATH, quality=60)

        # type=3 送出点赞, type=5 收到点赞
        given_likes = None
        received_likes = None
        if data.summary and data.summary.other:
            for item in data.summary.other:
                if item.type == 3:
                    given_likes = item.nums
                elif item.type == 5:
                    received_likes = item.nums

        context = {
            "data": data,
            "user_avatar": user_avatar,
            "time_type": TIME_TYPE_MAP.get(
                data.page2.oftenUseTimeType, "未知"
            ) if data.page2 else "未知",
            "latest_time": format_latest_time(
                data.page2.latestEnterTime
            ) if data.page2 and data.page2.latestEnterTime else "",
            "given_likes": given_likes,
            "received_likes": received_likes,
            "card_b64": card_b64,
            "logo_b64": get_logo_b64(),
            "footer_b64": get_footer_b64(),
        }

        if not PLAYWRIGHT_AVAILABLE:
            return _text_fallback(data)

        img = await render_html(waves_templates, "data_review_card.html", context)
        if img:
            return img

        return _text_fallback(data)

    except Exception as e:
        logger.exception(f"[鸣潮] 年度报告渲染失败: {e}")
        return f"生成年度报告失败: {e}"


def _text_fallback(data: DataReview) -> str:
    lines = [f"库街区年度航行报告 - {data.userName or '未知'}"]
    if data.page1:
        if data.page1.registerTime:
            lines.append(f"首次进入库街区: {data.page1.registerTime}")
        if data.page1.loginDay:
            lines.append(f"共登录: {data.page1.loginDay}天")
        if data.page1.maxContinueSignDay:
            lines.append(f"最高连签: {data.page1.maxContinueSignDay}天")
        if data.page1.signScorePercent:
            lines.append(f"超过了{data.page1.signScorePercent}%的库友")
    if data.page5:
        if data.page5.incomeCoin:
            lines.append(f"共获得: {data.page5.incomeCoin}库洛币")
    return "\n".join(lines)
