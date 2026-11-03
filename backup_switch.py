from netmiko import ConnectHandler
from netmiko import NetmikoTimeoutException, NetmikoAuthenticationException
import datetime
import getpass
import os
import difflib
import paramiko # For SFTP/SCP file transfer

# ================= Global Variables =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
switches_file = os.path.join(BASE_DIR, 'switch_list.txt')
backup_dir = os.path.join(BASE_DIR, 'local_backups')
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
BACK_COMMAND = 'b'

if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

# ================= Helper Functions =================

def get_input_with_back(prompt):
    """Get input from user with a 'back' option."""
    user_input = input(prompt + " (or 'b' to go back): ").strip()
    if user_input.lower() == BACK_COMMAND:
        return None 
    return user_input

def get_password_with_back(prompt):
    """Get password from user with a 'back' option."""
    pwd = getpass.getpass(prompt + " (or 'b' to go back): ")
    if pwd.lower() == BACK_COMMAND:
        return None
    return pwd

def read_switches_from_file():
    """Read the switch inventory list from the text file."""
    all_switches = []
    current_protocol = None
    try:
        with open(switches_file, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if line.upper() == '[SSH]':
                    current_protocol = 'cisco_ios'
                    continue
                elif line.upper() == '[TELNET]':
                    current_protocol = 'cisco_ios_telnet'
                    continue
                if current_protocol:
                    all_switches.append({'host': line, 'device_type': current_protocol})
    except FileNotFoundError:
        print(f"Error: The file {switches_file} was not found!")
        return []
    return all_switches

def perform_backup(ip, device_type, username, password, enable_secret, 
                   sftp_host, sftp_user, sftp_pass, sftp_path):
    """Connect, fetch config, save locally, and push to SFTP server securely."""
    proto_name = "Telnet" if device_type == 'cisco_ios_telnet' else "SSH"
    print(f"\n--- Backing up from {ip} (via {proto_name}) ---")
    
    device = {
        'device_type': device_type, 'host': ip,
        'username': username, 'password': password,
        'secret': enable_secret, 'timeout': 30,
    }

    if device_type == 'cisco_ios_telnet':
        device['global_delay_factor'] = 8
        device['fast_cli'] = False

    try:
        net_connect = ConnectHandler(**device)
        net_connect.enable()
        
        print(f"[{ip}] Fetching running-config...")
        running_config = net_connect.send_command("show running-config")
        
        # 1. Save the new config locally (for diffing)
        local_filename = f"{ip}-backup-{current_time}.cfg"
        local_filepath = os.path.join(backup_dir, local_filename)
        with open(local_filepath, 'w') as f:
            f.write(running_config)
        print(f"[{ip}] Saved locally to {local_filename}")

        # 2. Push to SFTP Server using Paramiko
        print(f"[{ip}] Pushing to SFTP Server ({sftp_host})...")
        try:
            transport = paramiko.Transport((sftp_host, 22))
            transport.connect(username=sftp_user, password=sftp_pass)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Construct the remote path
            remote_filepath = os.path.join(sftp_path, local_filename).replace("\\", "/")
            
            sftp.put(local_filepath, remote_filepath)
            print(f"[{ip}] Successfully uploaded to {remote_filepath}")
            
            sftp.close()
            transport.close()
        except Exception as sftp_error:
            print(f"[{ip}] SFTP Upload Error: {sftp_error}")
            # We still return True because the local backup succeeded, 
            # but we log the upload failure.
        
        net_connect.disconnect()
        return True 
        
    except NetmikoTimeoutException:
        print(f"[{ip}] Error: Connection timeout")
        return False
    except NetmikoAuthenticationException:
        print(f"[{ip}] Error: Authentication failed")
        return False
    except KeyboardInterrupt:
        print(f"\n[{ip}] Interrupted by user. Closing connection...")
        if 'net_connect' in locals():
            net_connect.disconnect()
        raise
    except Exception as e:
        print(f"[{ip}] Other Errors: {e}")
        return False

def show_diff_for_switch(ip):
    """Compare the two most recent local backups for a specific IP."""
    # (This function remains exactly the same as the previous version)
    print(f"\n--- Checking configuration changes for {ip} ---")
    previous_files = [f for f in os.listdir(backup_dir) if f.startswith(ip) and f.endswith('.cfg')]
    if len(previous_files) < 2:
        print(f"[{ip}] Not enough backups found locally to compare (need at least 2).")
        return
    previous_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
    latest_file = os.path.join(backup_dir, previous_files[0])
    older_file = os.path.join(backup_dir, previous_files[1])
    print(f"Comparing:\n  OLD: {previous_files[1]}\n  NEW: {previous_files[0]}\n")
    with open(older_file, 'r') as f_old: old_config = f_old.read()
    with open(latest_file, 'r') as f_new: new_config = f_new.read()

    def split_into_blocks(config):
        blocks = {}
        current_block_name = "GLOBAL_SETTINGS"
        current_lines = []
        for line in config.splitlines():
            if line.startswith("interface "):
                if current_lines: blocks[current_block_name] = current_lines
                current_block_name = line.strip()
                current_lines = [line]
            elif line.strip() == "!":
                if current_lines:
                    current_lines.append(line)
                    blocks[current_block_name] = current_lines
                current_block_name = "GLOBAL_SETTINGS"
                current_lines = []
            else:
                current_lines.append(line)
        if current_lines: blocks[current_block_name] = current_lines
        return blocks

    old_blocks = split_into_blocks(old_config)
    new_blocks = split_into_blocks(new_config)
    changes_found = False
    for block_name, new_lines in new_blocks.items():
        old_lines = old_blocks.get(block_name, [])
        if old_lines != new_lines:
            diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=previous_files[1], tofile=previous_files[0], lineterm='', n=3))
            if diff:
                changes_found = True
                print(f"\n--- Changes in: {block_name} ---")
                for line in diff:
                    if line.startswith('@@') or line.startswith('---') or line.startswith('+++'): continue
                    if line.startswith('+'): print(f"\033[92m{line.strip()}\033[0m")
                    elif line.startswith('-'): print(f"\033[91m{line.strip()}\033[0m")
                    else: print(f" {line.strip()}")
    for block_name in old_blocks:
        if block_name not in new_blocks:
            changes_found = True
            print(f"\n--- Removed Block: {block_name} ---")
    if not changes_found: print(f"[{ip}] No configuration changes detected between the last two backups.")
    else: print("\n" + "-" * 40)

def print_summary(success_list, failed_list):
    """Print the final backup summary."""
    print("\n" + "="*40)
    print("             BACKUP SUMMARY")
    print("="*40)
    print(f"\n✅ Successful Backups ({len(success_list)}):")
    for ip in success_list: print(f"  - {ip}")
    if not success_list: print("  None")
    print(f"\n❌ Failed Backups ({len(failed_list)}):")
    for ip in failed_list: print(f"  - {ip}")
    if not failed_list: print("  None")
    print("\n" + "="*40)

# ================= Main Application =================

def main():
    while True:
        print("\n" + "="*40)
        print("          SWITCH BACKUP TOOL MENU")
        print("="*40)
        print("1. Backup ALL switches from the list")
        print("2. Backup a SINGLE switch by IP")
        print("3. Show Configuration Changes (Diff) for an IP")
        print("4. Exit")
        print("="*40)
        
        choice = input("Select an option (1, 2, 3, or 4): ").strip()
        
        if choice == '4':
            print("Exiting... Goodbye!")
            break
        elif choice == '3':
            while True:
                target_ip = get_input_with_back("\nEnter the IP address to view changes")
                if target_ip is None: break
                show_diff_for_switch(target_ip)
                again = input("\nDo you want to check another switch? (y/n): ").strip().lower()
                if again != 'y': break
            continue
        
        elif choice not in ['1', '2']:
            print("Invalid option. Please choose 1, 2, 3, or 4.")
            continue

        success_list = []
        failed_list = []
        auth_success = False

        # --- Authentication & SFTP Details ---
        while True:
            print("\n=== Enter Switch Authentication Details (or 'b' to go back) ===")
            username = get_input_with_back("Switch Username")
            if username is None: break 
            
            password = get_password_with_back("Switch Password")
            if password is None: break
            
            enable_secret = get_password_with_back("Switch Enable secret (press Enter if same)")
            if enable_secret is None: break
            if not enable_secret: enable_secret = password

            print("\n=== Enter SFTP Server Details ===")
            sftp_host = get_input_with_back("SFTP Server IP/Hostname")
            if sftp_host is None: break
            
            sftp_user = get_input_with_back("SFTP Username")
            if sftp_user is None: break
            
            sftp_pass = get_password_with_back("SFTP Password")
            if sftp_pass is None: break
            
            sftp_path = get_input_with_back("SFTP Remote Directory (e.g., /backups/switches)")
            if sftp_path is None: break

            auth_success = True 
            break 

        if not auth_success:
            continue 

        if choice == '1':
            all_switches = read_switches_from_file()
            if not all_switches:
                print("Error: No switches found.")
                continue
            
            print(f"\nFound {len(all_switches)} switches. Starting full backup...")
            for sw in all_switches:
                is_success = perform_backup(
                    sw['host'], sw['device_type'], 
                    username, password, enable_secret,
                    sftp_host, sftp_user, sftp_pass, sftp_path
                )
                if is_success: success_list.append(sw['host'])
                else: failed_list.append(sw['host'])
            
            print_summary(success_list, failed_list)

        elif choice == '2':
            while True:
                target_ip = get_input_with_back("\nEnter the IP address of the target switch")
                if target_ip is None: break 

                all_switches = read_switches_from_file()
                target_device = next((sw for sw in all_switches if sw['host'] == target_ip), None)
                
                if target_device:
                    device_type = target_device['device_type']
                else:
                    print(f"Warning: {target_ip} is not in switch_list.txt.")
                    proto_choice = get_input_with_back("Is it [1] SSH or [2] Telnet?")
                    if proto_choice is None: break 
                    device_type = 'cisco_ios' if proto_choice == '1' else 'cisco_ios_telnet'

                is_success = perform_backup(
                    target_ip, device_type, 
                    username, password, enable_secret,
                    sftp_host, sftp_user, sftp_pass, sftp_path
                )
                if is_success: success_list.append(target_ip)
                else: failed_list.append(target_ip)
                
                print_summary(success_list, failed_list)
                again = input("\nDo you want to backup another switch? (y/n): ").strip().lower()
                if again != 'y': break

# ================= Start Program =================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Backup process interrupted by user (Ctrl+C). Exiting gracefully...")
        print("Goodbye!")
        exit(0)