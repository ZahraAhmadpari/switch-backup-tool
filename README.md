# Cisco Switch Backup Tool

A Python-based automation tool for securely backing up configuration files from Cisco switches over SSH or Telnet and uploading them to a remote SFTP server. The tool also includes a built-in diff engine to track configuration changes over time.

## Features

- **Multi-Protocol Support:** Connects to modern switches via SSH and legacy switches via Telnet.
- **Interactive Menu:** Provides a user-friendly CLI menu, with the option to go back (`b`) at any step.
- **Secure Authentication:** Prompts for passwords and enable secrets at runtime; no credentials are hardcoded.
- **Local and Remote Storage:** Saves a local copy for configuration comparison and uploads a copy to a remote SFTP server.
- **Configuration Diffing:** Compares the two most recent backups of a switch and displays changes grouped by configuration blocks, such as interfaces.
- **Graceful Interruption:** Handles `Ctrl+C` safely without displaying raw Python tracebacks.
- **Inventory Management:** Reads switch IP addresses from a simple text file (`switch_list.txt`).

## Prerequisites

- **Python 3.8 or later**
- **Netmiko** — for SSH and Telnet connections
- **Paramiko** — for SFTP uploads

Install the required Python libraries with pip:

```bash
pip install netmiko paramiko
```

## Project Structure

```text
switch-backup-tool/
│
├── backup_switch.py           # Main script
├── switch_list.txt.example    # Example switch inventory file
├── README.md                  # Project documentation
├── LICENSE                    # MIT License
├── .gitignore                 # Git ignore rules
└── legacy/                    # Older versions (e.g., the TFTP version)
```

## Setup and Usage

### 1. Prepare the Inventory File

Copy the example inventory file and rename it:

```bash
cp switch_list.txt.example switch_list.txt
```

Edit `switch_list.txt` and add your switch IP addresses under the appropriate protocol sections:

```ini
[SSH]
192.168.1.10
192.168.1.11

[TELNET]
192.168.1.50
```

### 2. Run the Script

Start the tool with:

```bash
python backup_switch.py
```

### 3. Use the Interactive Menu

The interactive menu guides you through the available operations:

```text
========================================
          SWITCH BACKUP TOOL MENU
========================================
1. Backup ALL switches from the list
2. Backup a SINGLE switch by IP
3. Show Configuration Changes (Diff) for an IP
4. Exit
========================================
```

#### Menu Options

- **Option 1 — Backup All Switches:** Backs up all switches listed in the inventory file.
- **Option 2 — Backup a Single Switch:** Backs up a specific switch by IP address. After the backup is complete, the tool asks whether you want to back up another switch, without requiring you to re-enter your credentials.
- **Option 3 — Show Configuration Changes (Diff):** Compares the two most recent backups for the specified IP address. Added lines are displayed in green, and removed lines are displayed in red.
- **Option 4 — Exit:** Closes the application.

**Navigation:** At any prompt, enter `b` to return to the main menu.

## How Configuration Diffing Works

The tool stores local backups in the `local_backups/` directory. Each backup filename includes the switch IP address and a timestamp. For example:

```text
192.168.1.10-backup-2026-11-03_14-30-15.cfg
```

When you select **Option 3**, the tool:

1. Finds all backup files associated with the specified IP address.
2. Sorts the files by their actual modification time.
3. Selects and compares the two most recent backups.
4. Splits the configuration into logical blocks, such as `interface GigabitEthernet1/0/18` and `GLOBAL_SETTINGS`.
5. Displays only the blocks that contain changes.

## Security Notes

- **No Hardcoded Credentials:** Switch and SFTP passwords are requested at runtime.
- **Secure SFTP Transfers:** Configuration files are uploaded using SFTP (SSH File Transfer Protocol), which encrypts data in transit.
- **Git Ignore Rules:** The actual switch inventory file (`switch_list.txt`) and local backups are excluded from Git to help prevent accidental exposure of sensitive information.
- **Local Backup Protection:** Backups are stored in the `local_backups/` directory on the local machine. Make sure this directory is protected with appropriate operating system permissions.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author

**Zahra Ahmadpari**  
GitHub: [@ZahraAhmadpari](https://github.com/ZahraAhmadpari)
