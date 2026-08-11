from pathlib import Path
from datetime import datetime

def get_dir_size(path: Path) -> int:
    """Рекурсивно вычисляет размер папки в байтах."""
    return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())

def log_msg(log_path: Path, msg: str):
    """Добавляет запись с отметкой времени в лог-файл."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")