from typing import Any, List

from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.button import WavesButton
from ..utils.database.models import WavesUser

login_fail = "[鸣潮] 登录失败，请稍后重试\n请检查库街区能否查询特征码[{}]的鸣潮账号数据"


async def login_success_msg(bot: Bot, ev: Event, waves_user: WavesUser):
    buttons: List[Any] = [
        WavesButton("体力", "mr"),
        WavesButton("刷新面板", "刷新面板"),
        WavesButton("深塔", "深塔"),
        WavesButton("冥歌海墟", "冥海"),
    ]

    from ..wutheringwaves_charinfo.draw_refresh_char_card import (
        draw_refresh_char_detail_img,
    )

    msg = await draw_refresh_char_detail_img(bot, ev, waves_user.user_id, waves_user.uid, buttons)
    if isinstance(msg, bytes):
        return await bot.send_option(msg, buttons)

    at_sender = True if ev.group_id else False
    uid = str(waves_user.uid or "")
    if uid.isdigit() and len(uid) == 9:
        text = login_fail.format(uid)
    else:
        text = "[鸣潮] 登录失败，请稍后重试\n"
    return await bot.send(text, at_sender=at_sender)
