# ⚡ FastZip

**FastZip** is a command-line utility designed to automate and optimize your workflow pipeline. 

The program handles the routine of preparing and sharing folders with other people: it automatically locates the target directory, neatly packages it into an archive, adds a timestamp to the filename, logs the process, and uploads the result to Google Drive with a single click, returning a ready-to-share link.

## ✨ Key Features

*   📦 **Smart Archiving:** Automatically packages a folder from a pre-configured source directory to a target destination.
*   🕒 **Versioning:** Adds a timestamp to the archive name for convenient sharing (e.g., `project_2026-08-19.zip`).
*   ☁️ **Cloud Integration:** Seamlessly uploads files directly to Google Drive.
*   🔗 **Quick Sharing:** Optional automatic read-access granting and generation of a public link for sharing.
*   📝 **Audit:** Keeps logs of all successful operations and errors.

---

## 🚀 Installation

The utility is installed globally for the user as an editable Python package, allowing it to run from anywhere in the terminal:

```bash
python3 -m pip install --user -e . --break-system-packages
```

---

## 💻 Usage

Basic command to pack a folder (the program will automatically find it in the configured `source_dir`):
```bash
fastzip <folder_name>
```

### 🛠 Flags and Attributes

| Flag | Description | Example Call |
| :--- | :--- | :--- |
| `-s`, `--source` | Changes the source directory for archives in the config | `fastzip -s /new/path/to/saves` |
| `-d`, `--dest` | Changes the destination directory for archives in the config | `fastzip -d /new/path/to/zips` |
| `-h`, `--help` | Shows the help message | `fastzip -h` |

---

## ⚙️ Configuration

Settings are stored in the `~/.config/fastzip/config.ini` file. Below are the available parameters for fine-tuning:

```ini
[paths]
source_dir = /path/to/source         # Where to look for folders
dest_dir = /path/to/archives         # Where to save the finished zip files

[google]
# Paths to authorization files
credentials_path = /home/miroslav/.config/fastzip/credentials.json
token_path = /home/miroslav/.config/fastzip/token.json

# Synchronization behavior
google_sync = true     # Enable the ability to upload to Google Drive
auto_sync = false      # Enable automatic upload (without the y/n prompt)
auto_share = false     # Enable automatic read-access and link generation
```

---

## ☁️ Google Cloud Setup

For the utility to be able to upload archives to the cloud, you need to connect an API key.

1. Create a project in the **Google Cloud Console**, enable the **Google Drive API**, and create an OAuth client (select the *Desktop app* type).
2. Download the generated JSON credentials file to your computer.
3. Move the downloaded file to the program's configuration folder and rename it:

```bash
mv ~/Downloads/your_long_file_name.json ~/.config/fastzip/credentials.json
```

On the first attempt to upload an archive, the script will request permission via your browser and automatically generate a `token.json` file. All subsequent uploads will happen automatically in the background.