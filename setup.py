#!/usr/bin/env python3
"""
Setup script for Live Stream Phone Extractor
Checks dependencies and helps with installation
"""

import sys
import subprocess
import os


def print_banner():
    print("""
+==================================================================+
|                                                                  |
|          LIVE STREAM PHONE EXTRACTOR - Setup                    |
|                                                                  |
+==================================================================+
""")


def check_python():
    """Check Python version"""
    print("[CHECK] Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print(f"[ERROR] Python 3.8+ required, found {version.major}.{version.minor}")
        return False


def check_playwright():
    """Check if playwright is installed"""
    print("[CHECK] Playwright module...")
    try:
        import playwright
        print(f"[OK] Playwright {playwright.__version__} installed")
        return True
    except ImportError:
        print("[MISSING] Playwright not installed")
        return False


def check_browser():
    """Check if Chromium is installed"""
    print("[CHECK] Chromium browser...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        print("[OK] Chromium browser ready")
        return True
    except Exception as e:
        print(f"[MISSING] Chromium not installed: {e}")
        return False


def install_playwright():
    """Install playwright"""
    print("\n[INSTALL] Installing playwright...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        print("[OK] Playwright installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install playwright: {e}")
        return False


def install_browser():
    """Install Chromium browser"""
    print("\n[INSTALL] Installing Chromium browser...")
    print("This may take a few minutes...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("[OK] Chromium installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install Chromium: {e}")
        return False


def create_output_dir():
    """Create output directory"""
    print("[SETUP] Creating output directory...")
    os.makedirs("output", exist_ok=True)
    print("[OK] Output directory ready")


def main():
    print_banner()
    
    print("Checking system requirements...\n")
    
    # Check Python
    if not check_python():
        print("\n[ERROR] Please install Python 3.8 or higher from https://python.org")
        input("\nPress Enter to exit...")
        return 1
    
    # Check Playwright
    has_playwright = check_playwright()
    
    # Check Browser
    has_browser = check_browser()
    
    print()
    
    # Install if needed
    if not has_playwright:
        if not install_playwright():
            print("\n[ERROR] Failed to install playwright")
            print("Try manually: pip install playwright")
            input("\nPress Enter to exit...")
            return 1
    
    if not has_browser:
        if not install_browser():
            print("\n[ERROR] Failed to install Chromium")
            print("Try manually: playwright install chromium")
            input("\nPress Enter to exit...")
            return 1
    
    # Setup directories
    create_output_dir()
    
    print("\n" + "="*66)
    print("[SUCCESS] Setup complete!")
    print("="*66)
    print("\nYou can now run the extractor:")
    print("  1. Double-click START.bat (Windows)")
    print("  2. Or run: python start.py")
    print("\nFor help, see QUICK_START.md")
    print()
    
    # Ask to run
    choice = input("Would you like to run the extractor now? (y/n): ").strip().lower()
    if choice == 'y':
        print("\nStarting extractor...\n")
        subprocess.call([sys.executable, "start.py"])
    else:
        input("\nPress Enter to exit...")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[Setup cancelled]")
        sys.exit(0)
