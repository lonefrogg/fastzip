import sys
import argparse
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

from fastzip.config import load_config, save_config
from fastzip.utils import get_dir_size, log_msg


def main():
    config = load_config()

    # Парсер аргументов
    parser = argparse.ArgumentParser(description="Быстрая упаковка папок в zip-архив с сохранением настроек.")
    parser.add_argument("folder_name", nargs="?", help="Имя папки для упаковки")
    parser.add_argument("-s", "--source", help="Установить новую директорию source_dir в конфиг навсегда")
    parser.add_argument("-d", "--dest", help="Установить новую директорию dest_dir в конфиг навсегда")
    args = parser.parse_args()

    # Обновление конфига
    config_updated = False

    if args.source:
        new_source_path = Path(args.source).resolve()

        if not new_source_path.is_dir():
            print(f"Ошибка: директория '{new_source_path}' не существует")
            sys.exit(1)

        config.set("paths", "source_dir", str(new_source_path))
        print(f"Настройка обновлена: source_dir = {new_source_path}")
        config_updated = True

    if args.dest:
        new_dest_path = Path(args.dest).resolve()

        if not new_dest_path.is_dir():
            print(f"Ошибка: директория '{new_dest_path}' не существует")
            sys.exit(1)

        config.set("paths", "dest_dir", str(new_dest_path))
        print(f"Настройка обновлена: dest_dir = {new_dest_path}")
        config_updated = True

    if config_updated:
        save_config(config)
        if not args.folder_name:
            sys.exit(0)

    # Проверка позиционного аргумента для архивации
    if not args.folder_name:
        print("Ошибка: укажите имя папки для упаковки\n")
        parser.print_help()
        sys.exit(1)

    # Установка путей из конфига
    source_dir = Path(config.get("paths", "source_dir"))
    dest_dir = Path(config.get("paths", "dest_dir"))
    folder_name = args.folder_name
    target_path = source_dir / folder_name

    dest_dir.mkdir(parents=True, exist_ok=True)
    log_file = dest_dir / "zips.log"

    # Проверка существования директорий
    if not source_dir.is_dir():
        print(f"Ошибка: исходная директория '{source_dir}' не существует")
        log_msg(log_file, f"Ошибка: исходная директория '{source_dir}' не существует")
        sys.exit(1)

    if not target_path.is_dir():
        print(f"Ошибка: Папка '{folder_name}' не найдена в '{source_dir}'")
        log_msg(log_file, f"Ошибка: Папка '{folder_name}' не найдена в '{source_dir}'")
        sys.exit(1)

    # Проверка свободного места
    target_size = get_dir_size(target_path)
    free_space = shutil.disk_usage(dest_dir).free

    if target_size > free_space:
        print("Ошибка: на диске слишком мало места для создания архива")
        log_msg(log_file, f"Ошибка: недостаточно места. Требуется: {target_size} байт, свободно: {free_space} байт.")
        sys.exit(1)
    else:
        target_mb = round(target_size / 1048576)
        free_mb = round(free_space / 1048576)
        log_msg(log_file, f"Проверка места пройдена: папка весит ~{target_mb} МБ, доступно ~{free_mb} МБ.")

    # Формирование имени и проверка на перезапись
    current_date = datetime.now().strftime("%Y-%m-%d")
    archive_name = f"{folder_name}_{current_date}.zip"
    archive_path = dest_dir / archive_name

    if archive_path.exists():
        answer = input(f"Файл {archive_name} уже существует, перезаписать его? (y/n)\n").strip().lower()
        if answer == 'y':
            print("Удаляем старый архив...")
            archive_path.unlink()
        elif answer == 'n':
            print("Отмена. Пропускаю упаковку.")
            log_msg(log_file, f"Пропуск: архив '{archive_name}' уже существует (отмена перезаписи)")
            sys.exit(0)
        else:
            print("Неверный ввод. Ожидается y или n. Выход.")
            sys.exit(1)

    # Архивация
    print(f"Создаю архив {archive_name}...")

    result = subprocess.run(
        ["zip", "-r", "-q", "-y", str(archive_path), folder_name],
        cwd=source_dir
    )

    if result.returncode == 0:
        print(f"Успех! Архив сохранён: {archive_path}")
        log_msg(log_file, f"Успешно: '{folder_name}' упакован в '{archive_path}'")
    else:
        print("Произошла ошибка при создании архива.")
        log_msg(log_file, f"Ошибка: сбой команды zip при упаковке '{folder_name}'")
        sys.exit(1)


if __name__ == "__main__":
    main()