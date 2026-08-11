import sys
import argparse
import shutil
import subprocess
from operator import truediv
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

        sync_enabled = config.getboolean("google", "sync_enabled", fallback=False)
        if sync_enabled:
            answer = input("Сохранить файл на google drive? (y/n)\n").strip().lower()
            if answer == "y":
                credits_path = Path(config.get("google", "credentials_path"))
                token_path = Path(config.get("google", "token_path"))

                if not credits_path.exists():
                    print("Синхронизация включена, но не найден creditials.json")
                    print("mv ваш_файл ~/.config/fastzip/credentials.json")
                    sys.exit(1)
                else:
                    try:
                        from fastzip.drive import get_drive_service, upload_to_drive

                        print("Сохраняю файл в Google drive...")
                        service = get_drive_service(credits_path, token_path)
                        file_id = upload_to_drive(service, archive_path)

                        answer2 = input(f"Файл успешно загружен в Google Drive! (ID: {file_id}). Открыть доступ к нему по ссылке? (y/n)\n").strip().lower()
                        log_msg(log_file, f"Загружено в облако: {archive_name}")

                        if answer2 == "y":
                            try:
                                new_permission = {
                                    'type': 'anyone',
                                    'role': 'reader',
                                }
                                service.permissions().create(
                                    fileId = file_id,
                                    body = new_permission
                                ).execute()
                                shared_file_link = service.files().get(
                                    fileId=file_id,
                                    fields = 'webViewLink'
                                ).execute()
                                clean_link = shared_file_link.get('webViewLink')

                                print("Файл успешно расшарен!\n", clean_link)
                                sys.exit(0)

                            except Exception as e:
                                print(f"Ошибка при расшаривании файла: {e}")
                                log_msg(log_file, f"Ошибка при расшаривании файла: {e}")
                            sys.exit(1)

                        else:
                            print("Завершаю работу.")
                            sys.exit(0)

                    except Exception as e:
                        print(f"Ошибка при загрузке в облако: {e}")
                        log_msg(log_file, f"Ошибка загрузки в Google Drive: {e}")
                        sys.exit(1)
            else:
                print("Завершаю работу.")
                sys.exit(0)


    else:
        print("Произошла ошибка при создании архива.")
        log_msg(log_file, f"Ошибка: сбой команды zip при упаковке '{folder_name}'")
        sys.exit(1)

if __name__ == "__main__":
    main()