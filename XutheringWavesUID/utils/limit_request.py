from datetime import datetime
from ..wutheringwaves_config import WutheringWavesConfig

LAST_TIME = datetime.now()
LAST_COUNT = 0

def check_request_rate_limit() -> bool:
    if WutheringWavesConfig.get_config("EnableLimit").data is False:
        return False
    
    global LAST_TIME
    
    mode = WutheringWavesConfig.get_config("LimitMode").data
    count = WutheringWavesConfig.get_config("LimitCount").data
    now = datetime.now()
    over = False
    if mode == "每分钟":
        diff = now - LAST_TIME
        if diff.total_seconds() >= 60:
            LAST_COUNT = 0
    elif mode == "每小时":
        diff = now - LAST_TIME
        if diff.total_seconds() >= 3600:
            LAST_COUNT = 0
    elif mode == "每天":
        diff = now - LAST_TIME
        if diff.total_seconds() >= 3600 * 24:
            LAST_COUNT = 0
    if LAST_COUNT > count:
        over = True
    LAST_TIME = now
    if over == False:
        LAST_COUNT += 1
    return over
