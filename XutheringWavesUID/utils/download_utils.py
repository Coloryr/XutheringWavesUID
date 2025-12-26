import os
import shutil
import hashlib
from pathlib import Path

from gsuid_core.logger import logger


def count_files(directory: Path, pattern: str = "*") -> int:
    """统计目录下指定模式的文件数量"""
    if not directory.exists():
        return 0
    return sum(1 for file in directory.rglob(pattern) if file.is_file())


def get_file_hash(file_path):
    """计算单个文件的哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        hash_md5.update(f.read())
    return hash_md5.hexdigest()


def copy_if_different(src, dst, name, soft=False):
    """复制并返回是否有更新"""
    if not os.path.exists(src):
        logger.debug(f"[鸣潮] {name} 源目录不存在")
        return False

    src_path = Path(src)
    src_total_files = count_files(src_path, "*")
    dst_path = Path(dst)
    if dst_path.exists():
        dst_py_count = count_files(dst_path, "*.py")
        if src_total_files and dst_py_count >= src_total_files:
            return False

    needs_update = False

    for src_file in sorted(src_path.rglob("*")):
        if src_file.is_file():
            rel_path = src_file.relative_to(src)
            dst_file = Path(dst) / rel_path

            if not dst_file.exists():
                needs_update = True
                break

            if get_file_hash(src_file) != get_file_hash(dst_file):
                needs_update = True
                break

    if needs_update:
        try:
            if not soft:
                shutil.copytree(src, dst, dirs_exist_ok=True)
        except Exception:
            pass  # 没关系，只返回更新状态
        logger.info(f"[鸣潮] {name} 更新完成！")
        return True
    else:
        logger.debug(f"[鸣潮] {name} 无需更新")
        return False
