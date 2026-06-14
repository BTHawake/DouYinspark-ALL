import os, sys
from enum import Enum
import json
import logging
from utils.logger import setup_logger

logger = setup_logger(level=logging.DEBUG)

"""
是否启用调试模式
更详细的日志打印，浏览器操作可视化等
"""
DEBUG = True
config_cache = None
userData_cache = None


class Environment(Enum):
    GITHUBACTION = "GITHUB_ACTION"  # GitHub Action 运行
    LOCAL = "LOCAL"  # 本地代码运行
    PACKED = "PACKED"  # PyInstaller 打包运行

    def __str__(self):
        return self.value


def get_environment():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Environment.PACKED
    elif os.getenv("GITHUB_ACTIONS") == "true":
        return Environment.GITHUBACTION
    else:
        return Environment.LOCAL


def _load_config():
    """从 CONFIG 环境变量或 config.json 加载全部配置，解析一次后缓存"""
    global config_cache, userData_cache

    if config_cache is not None:
        return

    raw = os.getenv("CONFIG", "")
    full = {}

    if raw:
        try:
            full = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"CONFIG 环境变量不是合法的 JSON: {e}")
    else:
        # 从 config.json 文件加载（本地开发用）
        config_file = os.path.join(os.path.dirname(__file__), "..", "config.json")
        config_file = os.path.abspath(config_file)
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    full = json.load(f)
                logger.debug(f"从 {config_file} 加载配置")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"config.json 读取失败: {e}")

    config_cache = {
        "messageTemplate": full.get("messageTemplate", "[盖瑞]今日火花[加一]\\n—— [右边] 每日一言 [左边] ——\\n[API]"),
        "hitokotoTypes": full.get("hitokotoTypes", ["文学", "影视", "诗词", "哲学"]),
        "matchMode": full.get("matchMode", "nickname"),
        "groupMatchMode": full.get("groupMatchMode", "name"),
        "browserTimeout": int(full.get("browserTimeout", 120000)),
        "friendListTimeout": int(full.get("friendListTimeout", 2000)),
        "taskRetryTimes": int(full.get("taskRetryTimes", 3)),
        "logLevel": full.get("logLevel", "Info"),
    }

    userData_cache = []
    accounts = full.get("accounts", [])
    for account in accounts:
        username = account.get("username", "未知用户")
        unique_id = account.get("unique_id")
        if not unique_id:
            logger.warning(f"账户 {username} 缺少 unique_id，已跳过")
            continue

        cookies = account.get("cookies", [])
        if isinstance(cookies, str):
            try:
                cookies = json.loads(cookies)
            except json.JSONDecodeError:
                logger.warning(f"账户 {username} 的 cookies 不是合法的 JSON，已跳过")
                continue
        if not cookies:
            logger.warning(f"账户 {username} 的 cookies 为空，已跳过")
            continue

        userData_cache.append({
            "unique_id": unique_id,
            "username": username,
            "cookies": sanitize_cookies(cookies),
            "targets": account.get("targets", []),
            "groups": account.get("groups", []),
        })


def get_config():
    """获取配置信息"""
    _load_config()
    return config_cache


def sanitize_cookies(cookies):
    for cookie in cookies:
        if "sameSite" in cookie:
            cookie.pop("sameSite")
    return cookies


def get_userData():
    """获取用户数据列表"""
    _load_config()
    return userData_cache
