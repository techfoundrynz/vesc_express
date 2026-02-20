#!/usr/bin/env python3
import os
import sys
import subprocess
import glob
import re
import shutil

# Color setup
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_status(msg, color=Colors.OKBLUE):
    print(f"{color}{msg}{Colors.ENDC}")

def get_hw_configs():
    configs = []
    # Find all hw_*.h files
    files = glob.glob("main/hwconf/**/hw_*.h", recursive=True)
    
    for f in files:
        hw_name = None
        hw_target = None
        
        try:
            with open(f, 'r') as header:
                content = header.read()
                
                # Extract HW_NAME
                name_match = re.search(r'#define\s+HW_NAME\s+"(.*?)"', content)
                if name_match:
                    hw_name = name_match.group(1)
                
                # Extract HW_TARGET
                target_match = re.search(r'#define\s+HW_TARGET\s+"(.*?)"', content)
                if target_match:
                    hw_target = target_match.group(1)
            
            if hw_name and hw_target:
                configs.append({
                    'name': hw_name,
                    'target': hw_target,
                    'file': f
                })
        except Exception as e:
            print(f"Error parseing {f}: {e}")
            
    # Sort configs by target (SoC) first, then by name
    # This groups builds by architecture (e.g. all C3s, then all S3s)
    configs.sort(key=lambda x: (x['target'], x['name']))
            
    return configs

def build_target(config, output_dir):
    build_dir = "build"
    
    print_status(f"\n========================================")
    print_status(f"Building: {config['name']} ({config['target']})")
    print_status(f"Config: {config['file']}")
    print_status(f"Dir: {build_dir}")
    print_status(f"========================================")
    
    # 1. Set Target
    cmd_base = ["idf.py", "-B", build_dir, f"-DHW_NAME={config['name']}"]
    
    print_status("--> Setting target...")
    res = subprocess.run(cmd_base + ["set-target", config['target']], shell=True if os.name == 'nt' else False)
    if res.returncode != 0:
        return False
        
    # 2. Build
    print_status("--> Building...")
    res = subprocess.run(cmd_base + ["build"], shell=True if os.name == 'nt' else False)
    
    if res.returncode == 0:
        print_status(f"SUCCESS: {config['name']}", Colors.OKGREEN)
        
        # 3. Copy artifacts
        try:
            # Create target-specific output directory
            target_output_dir = os.path.join(output_dir, config['name'])
            os.makedirs(target_output_dir, exist_ok=True)
            
            # Source paths
            src_bin = os.path.join(build_dir, "vesc_express.bin")
            src_boot = os.path.join(build_dir, "bootloader", "bootloader.bin")
            src_pt = os.path.join(build_dir, "partition_table", "partition-table.bin")

            # Copy Bin
            if os.path.exists(src_bin):
                shutil.copy2(src_bin, os.path.join(target_output_dir, "vesc_express.bin"))
                print_status(f"--> Copied bin to {target_output_dir}")
                
            # Copy Bootloader
            if os.path.exists(src_boot):
                shutil.copy2(src_boot, os.path.join(target_output_dir, "bootloader.bin"))
                print_status(f"--> Copied bootloader to {target_output_dir}")
            
            # Copy Partition Table
            if os.path.exists(src_pt):
                shutil.copy2(src_pt, os.path.join(target_output_dir, "partition_table.bin"))
                print_status(f"--> Copied partition table to {target_output_dir}")
            
        except Exception as e:
            print_status(f"Warning: Failed to copy artifacts: {e}", Colors.WARNING)
            
        return True
    else:
        print_status(f"FAILED: {config['name']}", Colors.FAIL)
        return False

def main():
    if not os.path.exists("main/hwconf"):
        print_status("Error: main/hwconf directory not found", Colors.FAIL)
        sys.exit(1)
        
    # Prepare output directory
    output_dir = "build_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print_status(f"Created output directory: {output_dir}")
        
    configs = get_hw_configs()
    print_status(f"Found {len(configs)} hardware configurations.")
    
    success_count = 0
    failed_configs = []
    
    for config in configs:
        if build_target(config, output_dir):
            success_count += 1
        else:
            failed_configs.append(config['name'])
            
    print("\n" + "="*40)
    print(f"Build Summary: {success_count}/{len(configs)} Succeeded")
    print(f"Artifacts: {os.path.abspath(output_dir)}")
    
    if failed_configs:
        print_status(f"Failed: {', '.join(failed_configs)}", Colors.FAIL)
        sys.exit(1)
    else:
        print_status("All builds successful!", Colors.OKGREEN)
        sys.exit(0)

if __name__ == "__main__":
    main()
