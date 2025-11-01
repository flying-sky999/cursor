# -*- coding: utf-8 -*-

"""
Video Upload Test Script
???? Pika PikaSwap ??????
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright


# Configuration
USER_DATA_DIR = str(Path.home() / "pika_playwright_profile")
PIKA_APP_URL = "https://pika.art/app"
TEST_VIDEO = r"/Users/helensliang/important/paper-data-ppt/InstructBench/pika/source"  # ?????????

ACTION_TIMEOUT = 60_000


def test_upload(page, video_path: str):
    """Test all possible upload methods"""
    
    print("\n" + "="*60)
    print("TESTING VIDEO UPLOAD")
    print("="*60)
    
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"[ERROR] Video not found: {video_path}")
        return
    
    print(f"\n[INFO] Testing with video: {video_file.name}")
    print(f"[INFO] Size: {video_file.stat().st_size / (1024*1024):.2f} MB")
    
    # Take initial screenshot
    page.screenshot(path="screenshot_initial.png")
    print("[SAVED] screenshot_initial.png")
    
    # Check page elements
    print("\n" + "-"*60)
    print("CHECKING PAGE ELEMENTS")
    print("-"*60)
    
    elements_check = {
        "input[type='file']": "File inputs",
        "label": "Labels",
        "form": "Forms",
        "#modify-region-video": "Specific video input",
        "label[for='modify-region-video']": "Label for video input",
        "div.group.relative.flex": "Upload icon divs",
    }
    
    for selector, description in elements_check.items():
        try:
            count = page.locator(selector).count()
            visible_count = 0
            for i in range(count):
                if page.locator(selector).nth(i).is_visible():
                    visible_count += 1
            print(f"[FOUND] {description}: {count} total, {visible_count} visible")
            
            # Print attributes for debugging
            if count > 0 and visible_count > 0:
                try:
                    for i in range(min(count, 3)):  # Check first 3 elements
                        elem = page.locator(selector).nth(i)
                        if elem.is_visible():
                            html = elem.evaluate("el => el.outerHTML")
                            print(f"  Element {i}: {html[:150]}...")
                except Exception as e:
                    print(f"  Could not get element details: {e}")
        except Exception as e:
            print(f"[ERROR] {description}: {e}")
    
    # Try each upload method
    print("\n" + "-"*60)
    print("TESTING UPLOAD METHODS")
    print("-"*60)
    
    methods_to_test = [
        ("Direct #modify-region-video", lambda: page.set_input_files("#modify-region-video", str(video_file))),
        ("Direct input[type='file']", lambda: page.set_input_files("input[type='file']", str(video_file))),
        ("Click label[for='modify-region-video']", lambda: click_and_upload(page, "label[for='modify-region-video']", video_file)),
        ("Click form label", lambda: click_and_upload(page, "form label", video_file)),
        ("Click div.group.relative.flex", lambda: click_and_upload(page, "div.group.relative.flex", video_file)),
    ]
    
    for method_name, method_func in methods_to_test:
        print(f"\n[TEST] {method_name}...")
        try:
            method_func()
            time.sleep(2)
            print(f"  ? No exception raised")
            
            # Take screenshot after each attempt
            screenshot_name = f"screenshot_{method_name.replace(' ', '_')}.png"
            page.screenshot(path=screenshot_name)
            print(f"  [SAVED] {screenshot_name}")
        except Exception as e:
            print(f"  ? Failed: {e}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


def click_and_upload(page, selector: str, video_file: Path):
    """Helper to click element and upload file"""
    with page.expect_file_chooser(timeout=15_000) as chooser:
        page.click(selector)
    chooser.value.set_files(str(video_file))


def main():
    # Get video path from command line or use default
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # List available videos
        video_dir = Path(TEST_VIDEO)
        if video_dir.is_dir():
            videos = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.mov"))
            if videos:
                video_path = str(videos[0])
                print(f"[INFO] Using first video found: {video_path}")
            else:
                print("[ERROR] No videos found in directory")
                print(f"[ERROR] Please provide video path: python test_video_upload.py <video_path>")
                return
        else:
            print("[ERROR] Please provide video path: python test_video_upload.py <video_path>")
            return
    
    with sync_playwright() as playwright:
        print("[INFO] Launching browser...")
        browser = playwright.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            accept_downloads=True,
        )
        
        page = browser.new_page()
        page.set_viewport_size({"width": 1420, "height": 900})
        page.set_default_timeout(ACTION_TIMEOUT)
        
        print(f"[INFO] Navigating to {PIKA_APP_URL}...")
        page.goto(PIKA_APP_URL, wait_until="domcontentloaded")
        time.sleep(3)
        
        # Click Pikaswaps
        print("[INFO] Clicking Pikaswaps button...")
        try:
            page.click("button:has-text('Pikaswaps')")
            print("[OK] Clicked Pikaswaps")
            time.sleep(4)  # Wait for interface to load
        except Exception as e:
            print(f"[ERROR] Could not click Pikaswaps: {e}")
            return
        
        # Run tests
        test_upload(page, video_path)
        
        print("\n[INFO] Browser will remain open. Press Ctrl+C to exit...")
        try:
            time.sleep(600)
        except KeyboardInterrupt:
            print("\n[INFO] Closing browser...")
        
        browser.close()


if __name__ == "__main__":
    main()
