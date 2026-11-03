# Cisco Switch Backup Tool

A Python-based automation tool to securely back up configuration files from Cisco switches (supporting both SSH and Telnet) and upload them to a remote SFTP server. It also includes a built-in diff engine to track configuration changes over time.

## Features

- **Multi-Protocol Support:** Connects to modern switches via SSH and legacy switches via Telnet.
- **Interactive Menu:** User-friendly CLI menu with the ability to go back (`b`) at any step.
- **Secure Authentication:** Prompts for passwords and enable secrets at runtime (no hardcoded credentials).
- **Local & Remote Storage:** Saves a local copy for diffing and uploads a secure copy to an SFTP server.
- **Configuration Diffing:** Compare the two most recent backups of any switch to see exactly what changed, grouped by interface blocks.
- **Graceful Interruption:** Safely handles `Ctrl+C` without throwing raw Python tracebacks.
- **Inventory Management:** Reads the list of switches from a simple, readable text file (`switch_list.txt`).

## Prerequisites

- **Python 3.8+**
- **Netmiko** (for SSH/Telnet connections)
- **Paramiko** (for SFTP uploads)

You can install the required libraries using pip:
```bash
pip install netmiko paramiko
```

Project Structure
```text
switch-backup-tool/
│
├── backup_switch.py           # The main script
├── switch_list.txt.example    # Example inventory file
├── README.md                  # This file
├── LICENSE                    # MIT License
├── .gitignore                 # Git ignore rules
└── legacy/                    # Older versions (e.g., TFTP version)


Setup & Usage

1. Prepare the Inventory File

Copy the example file and add your switches:
cp switch_list.txt.example switch_list.txt

Edit switch_list.txt and add your IPs under the appropriate section:
[SSH]
192.168.1.10
192.168.1.11

[TELNET]
192.168.1.50

2. Run the Script

python backup_switch.py

3. Follow the Menu

The interactive menu will guide you through the process:

========================================
          SWITCH BACKUP TOOL MENU
========================================
1. Backup ALL switches from the list
2. Backup a SINGLE switch by IP
3. Show Configuration Changes (Diff) for an IP
4. Exit
========================================

Option 1: Backs up all switches in the inventory file.

Option 2: Backs up a specific switch. After finishing, it asks if you want to back up another one (without re-entering credentials).

Option 3: Compares the two most recent backups of a specific switch and displays the changes in green (added) and red (removed).

b command: At any prompt, type b to go back to the main menu.


How the Diffing Works
The script saves local backups in the local_backups/ directory with timestamps (e.g., 192.168.1.10-backup-2026-11-03_14-30-15.cfg). When you select Option 3, it:

Finds all backups for the target IP.

Sorts them by actual modification time.

Compares the two most recent files.

Splits the configuration into logical blocks (e.g., interface GigabitEthernet1/0/18, GLOBAL_SETTINGS) and only shows the blocks that have changed.

Security Notes
No Hardcoded Credentials: Switch and SFTP passwords are prompted at runtime.

SFTP Transfer: All configuration files are uploaded to the remote server using SFTP (SSH File Transfer Protocol), ensuring encryption in transit.

.gitignore: The actual switch inventory (switch_list.txt) and local backups are excluded from Git to prevent accidental leaks.

Local Backups: Backups are stored in local_backups/ on the local machine. Ensure this directory is protected by OS-level permissions.

License
This project is licensed under the MIT License - see the LICENSE file for details.

Author
Zahra Ahmadpari
GitHub: @ZahraAhmadpari
