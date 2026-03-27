#!/usr/bin/env python3
"""
Stream Phone Extractor - Startup Launcher
Easy-to-use interface for running the scraper
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Banner
BANNER = """
+==================================================================+
|                                                                  |
|          LIVE STREAM PHONE EXTRACTOR v2.0                       |
|                                                                  |
|          Extract phone numbers from live streams                |
|                                                                  |
+==================================================================+
"""

def clear_screen():
    """Clear the console"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    """Print main menu"""
    print(BANNER)
    print("\nMAIN MENU:\n")
    print("  [1] Quick Start (2 minutes)")
    print("  [2] Standard Run (5 minutes)")
    print("  [3] Extended Run (15 minutes)")
    print("  [4] Custom Duration")
    print("  [5] View Previous Results")
    print("  [6] Change Target URL")
    print("  [7] Open Output Folder")
    print("  [0] Exit")
    print("\n" + "="*66)

def get_current_url():
    """Get current target URL from config"""
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config.get('url', 'https://live.leisu.com/detail-4455336')
    return 'https://live.leisu.com/detail-4455336'

def save_url(url):
    """Save URL to config"""
    config = {'url': url, 'last_updated': datetime.now().isoformat()}
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

def run_scraper(duration, url=None):
    """Run the scraper with specified duration"""
    if url is None:
        url = get_current_url()
    
    print(f"\n{'='*66}")
    print(f"[START] Starting scraper...")
    print(f"[URL] Target: {url}")
    print(f"[TIME] Duration: {duration} seconds ({duration//60} minutes)")
    print(f"{'='*66}\n")
    
    try:
        # Import and run the production scraper
        from production_scraper import ProductionScraper
        
        scraper = ProductionScraper([url], output_dir="./output")
        scraper.run(duration_per_url=duration)
        
        print(f"\n{'='*66}")
        print("[SUCCESS] Scraping completed successfully!")
        print(f"{'='*66}\n")
        
        # Show latest results
        show_latest_results()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("Please check if all dependencies are installed:")
        print("  pip install playwright")
        print("  playwright install chromium")

def show_latest_results():
    """Show the most recent extraction results"""
    output_dir = Path("./output")
    
    if not output_dir.exists():
        print("❌ No output folder found yet.")
        return
    
    # Find latest JSON file
    json_files = sorted(output_dir.glob("phones_*.json"), reverse=True)
    
    if not json_files:
        print("[INFO] No results found yet.")
        return
    
    latest = json_files[0]
    
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"[RESULTS] Latest: {latest.name}")
        print(f"   Total phones: {data.get('total', 0)}")
        print(f"   Timestamp: {data.get('timestamp', 'N/A')[:19]}")
        
        phones = list(data.get('phones', {}).keys())
        if phones:
            print(f"\n[PHONES] Sample numbers:")
            for phone in sorted(phones)[:10]:
                formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                print(f"   - {formatted}")
            
            if len(phones) > 10:
                print(f"   ... and {len(phones) - 10} more")
        
        # Also show text file location
        txt_file = latest.name.replace('.json', '.txt')
        print(f"\n[FILE] Full list saved to: output/{txt_file}")
        
    except Exception as e:
        print(f"[ERROR] Reading results: {e}")

def view_all_results():
    """View all previous extraction results"""
    output_dir = Path("./output")
    
    if not output_dir.exists():
        print("[INFO] No output folder found.")
        return
    
    json_files = sorted(output_dir.glob("phones_*.json"), reverse=True)
    
    if not json_files:
        print("❌ No results found.")
        return
    
    print(f"\n[HISTORY] EXTRACTION HISTORY ({len(json_files)} runs)\n")
    print(f"{'#':<4} {'Date':<20} {'Phones':<10} {'File'}")
    print("-" * 66)
    
    for i, file in enumerate(json_files[:20], 1):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            timestamp = data.get('timestamp', 'N/A')[:19].replace('T', ' ')
            total = data.get('total', 0)
            print(f"{i:<4} {timestamp:<20} {total:<10} {file.name}")
        except:
            print(f"{i:<4} {'Error reading':<20} {'?':<10} {file.name}")
    
    print()
    
    # Option to view details
    choice = input("Enter number to view details (or press Enter to go back): ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(json_files):
            show_file_details(json_files[idx])

def show_file_details(file_path):
    """Show details of a specific result file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n{'='*66}")
        print(f"[FILE] {file_path.name}")
        print(f"{'='*66}")
        print(f"Total phones: {data.get('total', 0)}")
        print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        print(f"\nAll phone numbers:\n")
        
        phones = list(data.get('phones', {}).keys())
        for phone in sorted(phones):
            formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
            print(f"  {formatted}")
        
        print(f"\n{'='*66}\n")
        
    except Exception as e:
        print(f"[ERROR] {e}")

def change_url():
    """Change the target URL"""
    current = get_current_url()
    
    print(f"\nCurrent URL: {current}")
    print("\nExample URLs:")
    print("  https://live.leisu.com/detail-4455336")
    print("  https://live.leisu.com/detail-4244416")
    
    new_url = input("\nEnter new URL (or press Enter to keep current): ").strip()
    
    if new_url:
        if new_url.startswith('http'):
            save_url(new_url)
            print(f"[OK] URL updated to: {new_url}")
        else:
            print("[ERROR] Invalid URL. Must start with http:// or https://")
    else:
        print("URL unchanged.")

def open_output_folder():
    """Open the output folder"""
    output_dir = Path("./output").absolute()
    
    if not output_dir.exists():
        output_dir.mkdir(exist_ok=True)
    
    print(f"\n[OPEN] {output_dir}")
    
    try:
        if os.name == 'nt':  # Windows
            os.startfile(output_dir)
        elif os.name == 'posix':  # macOS/Linux
            os.system(f'open "{output_dir}"' if sys.platform == 'darwin' else f'xdg-open "{output_dir}"')
        print("[OK] Folder opened!")
    except Exception as e:
        print(f"[ERROR] Could not open folder: {e}")
        print(f"   Please navigate to: {output_dir}")

def custom_duration():
    """Get custom duration from user"""
    print("\n[CUSTOM] CUSTOM DURATION")
    print("-" * 66)
    print("Enter duration in minutes:")
    print("  1-5   = Quick scan")
    print("  5-15  = Standard run")
    print("  15-60 = Deep scan")
    
    try:
        minutes = float(input("\nDuration (minutes): ").strip())
        if minutes <= 0:
            print("[ERROR] Duration must be positive.")
            return None
        if minutes > 120:
            confirm = input(f"[WARNING] {minutes} minutes is very long. Continue? (y/n): ").strip().lower()
            if confirm != 'y':
                return None
        
        return int(minutes * 60)
    except ValueError:
        print("[ERROR] Invalid input. Please enter a number.")
        return None

def main():
    """Main entry point"""
    # Ensure output directory exists
    Path("./output").mkdir(exist_ok=True)
    
    while True:
        clear_screen()
        print_menu()
        
        choice = input("Enter your choice: ").strip()
        
        if choice == '1':
            # Quick start - 2 minutes
            clear_screen()
            run_scraper(120)
            input("\n[Press Enter to continue...]")
            
        elif choice == '2':
            # Standard - 5 minutes
            clear_screen()
            run_scraper(300)
            input("\n[Press Enter to continue...]")
            
        elif choice == '3':
            # Extended - 15 minutes
            clear_screen()
            print("\n[WARNING] This will run for 15 minutes.")
            confirm = input("Are you sure? (y/n): ").strip().lower()
            if confirm == 'y':
                run_scraper(900)
            input("\n[Press Enter to continue...]")
            
        elif choice == '4':
            # Custom duration
            clear_screen()
            duration = custom_duration()
            if duration:
                run_scraper(duration)
            input("\n[Press Enter to continue...]")
            
        elif choice == '5':
            # View results
            clear_screen()
            view_all_results()
            input("\n[Press Enter to continue...]")
            
        elif choice == '6':
            # Change URL
            clear_screen()
            change_url()
            input("\n[Press Enter to continue...]")
            
        elif choice == '7':
            # Open output folder
            open_output_folder()
            input("\n[Press Enter to continue...]")
            
        elif choice == '0':
            # Exit
            print("\n[Goodbye!]\n")
            sys.exit(0)
            
        else:
            print("\n[ERROR] Invalid choice. Please try again.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Goodbye!]")
        sys.exit(0)
