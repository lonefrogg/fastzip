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
    parser = argparse.ArgumentParser(description="Quick packaging of folders into a zip archive with settings preserved.")
    parser.add_argument("folder_name", nargs="?", help="Folder name to pack")
    parser.add_argument("-s", "--source", help="Set new source_dir directory in config permanently")
    parser.add_argument("-d", "--dest", help="Set new dest_dir directory in config permanently")
    args = parser.parse_args()

    # Обновление конфига
    config_updated = False

    if args.source:
        new_source_path = Path(args.source).resolve()

        if not new_source_path.is_dir():
            print(f"Error: directory '{new_source_path}' does not exist")
            sys.exit(1)

        config.set("paths", "source_dir", str(new_source_path))
        print(f"Setting updated: source_dir = {new_source_path}")
        config_updated = True

    if args.dest:
        new_dest_path = Path(args.dest).resolve()

        if not new_dest_path.is_dir():
            print(f"Error: directory '{new_dest_path}' does not exist")
            sys.exit(1)

        config.set("paths", "dest_dir", str(new_dest_path))
        print(f"Setting updated: dest_dir = {new_dest_path}")
        config_updated = True

    if config_updated:
        save_config(config)
        if not args.folder_name:
            sys.exit(0)

    # Проверка позиционного аргумента для архивации
    if not args.folder_name:
        print("Error: specify the folder name to pack\n")
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
        print(f"Error: source directory '{source_dir}' does not exist")
        log_msg(log_file, f"Error: source directory '{source_dir}' does not exist")
        sys.exit(1)

    if not target_path.is_dir():
        print(f"Error: folder '{folder_name}' not found in '{source_dir}'")
        log_msg(log_file, f"Error: folder '{folder_name}' not found in '{source_dir}'")
        sys.exit(1)

    # Проверка свободного места
    target_size = get_dir_size(target_path)
    free_space = shutil.disk_usage(dest_dir).free

    if target_size > free_space:
        print("Error: not enough disk space to create the archive")
        log_msg(log_file, f"Error: not enough space. Required: {target_size} bytes, free: {free_space} bytes.")
        sys.exit(1)
    else:
        target_mb = round(target_size / 1048576)
        free_mb = round(free_space / 1048576)
        log_msg(log_file, f"Space check passed: folder size is ~{target_mb} MB, available ~{free_mb} MB.")

    # Формирование имени и проверка на перезапись
    current_date = datetime.now().strftime("%Y-%m-%d")
    archive_name = f"{folder_name}_{current_date}.zip"
    archive_path = dest_dir / archive_name

    if archive_path.exists():
        answer = input(f"File {archive_name} already exists, overwrite it? (y/n)\n").strip().lower()
        if answer == 'y':
            print("Removing old archive...")
            archive_path.unlink()
        elif answer == 'n':
            print("Cancelled. Skipping packing.")
            log_msg(log_file, f"Skipped: archive '{archive_name}' already exists (overwrite cancelled)")
            sys.exit(0)
        else:
            print("Invalid input. Expected y or n. Exiting.")
            sys.exit(1)

    # Архивация
    print(f"Creating archive {archive_name}...")

    result = subprocess.run(
        ["zip", "-r", "-q", "-y", str(archive_path), folder_name],
        cwd=source_dir
    )

    if result.returncode == 0:
        print(f"Success! Archive saved: {archive_path}")
        log_msg(log_file, f"Success: '{folder_name}' packed into '{archive_path}'")

        sync_enabled = config.getboolean("google", "google_sync", fallback=False)
        if sync_enabled:

            if config.getboolean("google", "auto_sync", fallback=False):
                answer = 'y'
            else:
                answer = input("Save file to Google Drive? (Y/N)\n").strip().lower()

            if answer == "y" or answer == "Y":
                credits_path = Path(config.get("google", "credentials_path"))
                token_path = Path(config.get("google", "token_path"))

                if not credits_path.exists():
                    print("Synchronization is enabled, but creditials.json not found")
                    print("mv your_file ~/.config/fastzip/credentials.json")
                    sys.exit(1)
                else:
                    try:
                        from fastzip.drive import get_drive_service, upload_to_drive

                        print("Saving file to Google Drive...")
                        service = get_drive_service(credits_path, token_path)
                        file_id = upload_to_drive(service, archive_path)

                        if config.getboolean("google", "auto_share", fallback=False):
                            answer2 = "y"
                        else:
                            answer2 = input(f"File successfully uploaded to Google Drive! (ID: {file_id}). Share it via link? (Y/N)\n").strip().lower()
                        log_msg(log_file, f"Uploaded to cloud: {archive_name}")

                        if answer2 == "y" or answer2 == "Y":
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
                                print(f"Access successfully granted: {clean_link}")
                                log_msg(log_file, f"Access successfully granted: {clean_link}")

                                sys.exit(0)

                            except Exception as e:
                                print(f"Error granting access to the file: {e}")
                                log_msg(log_file, f"Error granting access to the file: {e}")
                            sys.exit(1)

                        else:
                            print("Exiting.")
                            sys.exit(0)

                    except Exception as e:
                        print(f"Error uploading to cloud: {e}")
                        log_msg(log_file, f"Error uploading to cloud: {e}")
                        sys.exit(1)
            else:
                print("Exiting.")
                sys.exit(0)


    else:
        print("An error occurred while creating the archive.")
        log_msg(log_file, f"Error: zip command failed while packing '{folder_name}'")
        sys.exit(1)

if __name__ == "__main__":
    main()