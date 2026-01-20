import time
from typing import List, Union
from datetime import datetime

from gsuid_core.logger import logger
from ..utils.waves_api import waves_api
from ..wutheringwaves_config import PREFIX
from ..utils.resource.RESOURCE_PATH import waves_templates, ANN_CARD_PATH
from ..utils.render_utils import (
    PLAYWRIGHT_AVAILABLE,
    get_logo_b64,
    get_footer_b64,
    get_image_b64_with_cache,
    render_html,
)


from .ann_card import ann_list_card as ann_list_card_pil
from .ann_card import ann_detail_card as ann_detail_card_pil
from .ann_card import format_date


async def ann_list_card() -> bytes:
    if not PLAYWRIGHT_AVAILABLE:
        return await ann_list_card_pil()

    try:
        logger.debug("[鸣潮] 正在获取公告列表...")
        ann_list = await waves_api.get_ann_list()
        if not ann_list:
            raise Exception("获取游戏公告失败,请检查接口是否正常")

        grouped = {}
        for item in ann_list:
            t = item.get("eventType")
            if not t:
                continue
            grouped.setdefault(t, []).append(item)

        for data in grouped.values():
            data.sort(key=lambda x: x.get("publishTime", 0), reverse=True)

        CONFIGS = {
            1: {"name": "活动", "color": "#ff6b6b"},
            2: {"name": "资讯", "color": "#45b7d1"},
            3: {"name": "公告", "color": "#4ecdc4"}
        }
        
        sections = []
        for t in [1, 2, 3]:
            if t not in grouped:
                continue
            
            section_items = []
            for item in grouped[t][:6]:
                if not item.get("id") or not item.get("postTitle"):
                    continue

                # 将封面图 URL 转换为 base64（使用本地缓存）
                cover_url = item.get("coverUrl", "")
                cover_b64 = await get_image_b64_with_cache(cover_url, ANN_CARD_PATH) if cover_url else ""

                section_items.append({
                    "id": str(item.get("id", "")),
                    "postTitle": item.get("postTitle", ""),
                    "date_str": format_date(item.get("publishTime", 0)),
                    "coverUrl": cover_url,  # 保留原 URL 作为后备
                    "coverB64": cover_b64,   # base64 版本
                })
            
            if section_items:
                sections.append({
                    "name": CONFIGS[t]["name"],
                    "color": CONFIGS[t]["color"],
                    "ann_list": section_items
                })

        context = {
            "title": "鸣潮公告",
            "subtitle": f"查看详细内容，使用 {PREFIX}公告#ID 查看详情",
            "is_list": True,
            "sections": sections,
            "logo_b64": get_logo_b64(),
            "footer_b64": get_footer_b64()
        }

        logger.debug(f"[鸣潮] 准备通过HTML渲染列表, sections: {len(sections)}")
        img_bytes = await render_html(waves_templates, "ann_card.html", context)
        if img_bytes:
            return img_bytes
        else:
            logger.warning("[鸣潮] Playwright 渲染返回空, 正在回退到 PIL 渲染")
            return await ann_list_card_pil()

    except Exception as e:
        logger.exception(f"[鸣潮] HTML渲染失败: {e}")
        return await ann_list_card_pil()


async def ann_detail_card(ann_id: int, is_check_time=False) -> Union[bytes, str, List[bytes]]:
    if not PLAYWRIGHT_AVAILABLE:
        return await ann_detail_card_pil(ann_id, is_check_time)

    try:
        logger.debug(f"[鸣潮] 正在获取公告详情: {ann_id}")
        ann_list = await waves_api.get_ann_list(True)
        if not ann_list:
            raise Exception("获取游戏公告失败,请检查接口是否正常")
        
        content = [x for x in ann_list if x["id"] == ann_id]
        if not content:
            return "未找到该公告"

        postId = content[0]["postId"]
        res = await waves_api.get_ann_detail(postId)
        if not res:
            return "未找到该公告"

        if is_check_time:
            post_time = format_post_time(res["postTime"])
            now_time = int(time.time())
            if post_time < now_time - 86400:
                return "该公告已过期"

        post_content = res["postContent"]
        
        content_type2_first = [x for x in post_content if x["contentType"] == 2]
        if not content_type2_first and "coverImages" in res:
            _node = res["coverImages"][0]
            _node["contentType"] = 2
            post_content.insert(0, _node)

        if not post_content:
            return "未找到该公告"

        processed_content = []
        for item in post_content:
            ctype = item.get("contentType")
            if ctype == 1:
                processed_content.append({
                    "contentType": 1,
                    "content": item.get("content", "")
                })
            elif ctype == 2 and "url" in item:
                # 将图片 URL 转换为 base64（使用本地缓存）
                img_url = item["url"]
                img_b64 = await get_image_b64_with_cache(img_url, ANN_CARD_PATH)
                processed_content.append({
                    "contentType": 2,
                    "url": img_url,        # 保留原 URL 作为后备
                    "urlB64": img_b64,     # base64 版本
                })
            else:
                cover_url = item.get("coverUrl") or item.get("videoCoverUrl")
                if cover_url:
                    # 将视频封面 URL 转换为 base64（使用本地缓存）
                    cover_b64 = await get_image_b64_with_cache(cover_url, ANN_CARD_PATH)
                    processed_content.append({
                        "contentType": "video",
                        "coverUrl": cover_url,    # 保留原 URL 作为后备
                        "coverB64": cover_b64,     # base64 版本
                    })

        # 获取用户信息
        user_name = res.get("userName", "鸣潮")
        head_code_url = res.get("headCodeUrl", "")
        user_avatar = ""
        if head_code_url:
            user_avatar = await get_image_b64_with_cache(head_code_url, ANN_CARD_PATH)

        context = {
            "title": res.get("postTitle", "公告详情"),
            "subtitle": f"发布时间: {res.get('postTime', '未知')}",
            "post_time": res.get('postTime', '未知'),
            "user_name": user_name,
            "user_avatar": user_avatar,
            "is_list": False,
            "content": processed_content,
            "logo_b64": get_logo_b64(),
            "footer_b64": get_footer_b64()
        }

        logger.debug(f"[鸣潮] 准备通过HTML渲染详情, content items: {len(processed_content)}")
        img_bytes = await render_html(waves_templates, "ann_card.html", context)
        if img_bytes:
            return img_bytes
        else:
            logger.warning("[鸣潮] Playwright 渲染返回空, 正在回退到 PIL 渲染")
            return await ann_detail_card_pil(ann_id, is_check_time)

    except Exception as e:
        logger.exception(f"[鸣潮] HTML渲染失败: {e}")
        return await ann_detail_card_pil(ann_id, is_check_time)


def format_post_time(post_time: str) -> int:
    try:
        timestamp = datetime.strptime(post_time, "%Y-%m-%d %H:%M").timestamp()
        return int(timestamp)
    except ValueError:
        pass

    try:
        timestamp = datetime.strptime(post_time, "%Y-%m-%d %H:%M:%S").timestamp()
        return int(timestamp)
    except ValueError:
        pass

    return 0