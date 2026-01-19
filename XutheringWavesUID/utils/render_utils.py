import base64
from typing import Union, Optional
from pathlib import Path

from gsuid_core.logger import logger
from .resource.RESOURCE_PATH import TEMP_PATH


def _import_playwright():
    """导入并返回 playwright async_playwright

    Returns:
        async_playwright 模块或None（如果未安装）
    """
    try:
        from playwright.async_api import async_playwright
        return async_playwright
    except ImportError:
        logger.warning("[鸣潮] 未安装 playwright，无法使用渲染公告、wiki图等功能。")
        logger.info("[鸣潮] 安装方法 Linux/Mac: 在当前目录下执行 source .venv/bin/activate && uv pip install playwright && uv run playwright install chromium")
        logger.info("[鸣潮] 安装方法 Windows: 在当前目录下执行 .venv\\Scripts\\activate; uv pip install playwright; uv run playwright install chromium")
        return None


# 尝试导入 playwright
async_playwright = _import_playwright()
PLAYWRIGHT_AVAILABLE = async_playwright is not None


async def render_html(waves_templates, template_name: str, context: dict) -> Optional[bytes]:
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        return None

    try:
        logger.debug(f"[鸣潮] HTML渲染开始: {template_name}")
        logger.debug(f"[鸣潮] async_playwright type: {type(async_playwright)}")

        try:
            template = waves_templates.get_template(template_name)
            html_content = template.render(**context)
            logger.debug(f"[鸣潮] HTML渲染完成: {template_name}")
        except Exception as e:
            logger.error(f"[鸣潮] Template render failed: {e}")
            raise e

        try:
            logger.debug("[鸣潮] 进入 async_playwright 上下文...")
            async with async_playwright() as p:
                logger.debug("[鸣潮] 启动浏览器...")
                browser = await p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
                page = await browser.new_page(viewport={"width": 800, "height": 1000})

                logger.debug("[鸣潮] 加载HTML内容...")
                await page.set_content(html_content)

                try:
                    logger.debug("[鸣潮] 等待网络空闲...")
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception as e:
                    logger.debug(f"[鸣潮] 等待网络空闲超时 (可能部分资源加载缓慢): {e}")

                logger.debug("[鸣潮] 正在截图...")
                # Screenshot only the container element to avoid extra whitespace
                container = page.locator(".container")
                screenshot = await container.screenshot(type='jpeg', quality=90)

                await browser.close()
                logger.debug(f"[鸣潮] HTML渲染成功, 图片大小: {len(screenshot)} bytes")
                return screenshot
        except Exception as e:
            logger.error(f"[鸣潮] Playwright execution failed: {e}")
            raise e

    except Exception as e:
        logger.error(f"[鸣潮] HTML渲染失败: {e}")
        return None


def image_to_base64(image_path: Union[str, Path]) -> str:
    if not isinstance(image_path, Path):
        image_path = Path(image_path)
    if not image_path.exists():
        return ""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        ext = image_path.suffix.lstrip(".").lower()
        if ext == "jpg":
            ext = "jpeg"
        return f"data:image/{ext};base64,{base64.b64encode(data).decode('utf-8')}"
    except Exception as e:
        logger.warning(f"[渲染工具] 图片转 base64 失败: {image_path}, {e}")
        return ""


def get_logo_b64() -> Optional[str]:
    try:
        logo_path = TEMP_PATH / "imgs" / "kurobbs.png"

        if not logo_path.exists():
            return None

        with open(logo_path, "rb") as f:
            data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"
    except Exception as e:
        logger.warning(f"[渲染工具] Logo loading failed: {e}")
        return None


def get_footer_b64(footer_type: str = "black") -> Optional[str]:
    try:
        from pathlib import Path

        current_file_path = Path(__file__).resolve()
        footer_path = current_file_path.parent / "texture2d" / f"footer_{footer_type}.png"

        if not footer_path.exists():
            if footer_type == "black":
                footer_path = current_file_path.parent / "texture2d" / "footer_white.png"
            else:
                footer_path = current_file_path.parent / "texture2d" / "footer_black.png"

        if not footer_path.exists():
            return None

        with open(footer_path, "rb") as f:
            data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"
    except Exception as e:
        logger.warning(f"[渲染工具] Footer loading failed: {e}")
        return None


async def get_image_b64_with_cache(url: str, cache_path: Path) -> str:
    if not url:
        return ""

    try:
        from .image import pic_download_from_url

        await pic_download_from_url(cache_path, url)

        filename = url.split("/")[-1]
        local_path = cache_path / filename

        return image_to_base64(local_path)
    except Exception as e:
        logger.warning(f"[渲染工具] 获取图片 base64 失败: {url}, {e}")
        return ""
