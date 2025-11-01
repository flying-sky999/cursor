# Video Upload Debugging Guide

## Problem
Video upload step is failing in the Pika PikaSwap automation script.

## Improvements Made

### 1. Enhanced Main Script (`pika_pikaswap_automation.py`)

**Added comprehensive upload methods (4 methods):**

- **Method 1: Direct File Input** (Most reliable)
  - Tries `#modify-region-video`
  - Tries generic `input[type='file']`
  - Tries `input[accept*='video']`
  - Tries `form input[type='file']`

- **Method 2: Click Label Elements**
  - `label[for='modify-region-video']`
  - `form label`
  - Various nested label selectors
  - Tries all visible labels one by one

- **Method 3: Click Upload Icon Div**
  - `div.group.relative.flex.h-15.w-15`
  - `div.group.relative.flex:has(svg)`
  - Div with specific SVG icon

- **Method 4: JavaScript Injection**
  - Finds file input via JavaScript
  - Directly sets files

**Added debugging features:**
- File size display
- Element count detection (inputs, labels, forms)
- Detailed error messages for each method
- Screenshot capture before/after upload attempts
- HTML dump on failure
- Extended wait time after clicking Pikaswaps

### 2. Created Test Script (`test_video_upload.py`)

A standalone testing script to diagnose upload issues:

**Features:**
- Tests all upload methods systematically
- Takes screenshots after each attempt
- Shows detailed element information
- Lists all file inputs, labels, and forms on page
- Prints HTML snippets for debugging

**Usage:**
```bash
# Test with specific video
python test_video_upload.py /path/to/video.mp4

# Test with first video in default directory
python test_video_upload.py
```

**Output:**
- `screenshot_initial.png` - Page state when loaded
- `screenshot_<method_name>.png` - After each upload attempt
- Console output with detailed element information

## Debugging Steps

### Step 1: Run the test script
```bash
python test_video_upload.py /path/to/your/video.mp4
```

Check the console output to see:
- How many file inputs are found
- How many labels are found
- Which elements are visible
- Which upload method works

### Step 2: Check screenshots
Look at the generated screenshots to verify:
- Is the upload area visible?
- Is the page fully loaded?
- Are you in the correct Pikaswaps interface?

### Step 3: Examine HTML output
The script prints HTML snippets of found elements. Look for:
- The correct `id` or `for` attribute
- Hidden elements that might be interfering
- JavaScript event handlers

### Step 4: Common issues and solutions

**Issue: "Found 0 file input(s)"**
- Solution: Page not fully loaded. Increase wait time after clicking Pikaswaps.
- Check: Wait for specific element like `textarea#promptText` to ensure page is ready.

**Issue: "File chooser timeout"**
- Solution: Element is not clickable or wrong element.
- Check: Use screenshots to find the correct upload button/area.

**Issue: "Element is not visible"**
- Solution: Need to scroll or wait for animation.
- Check: Add explicit scroll or longer wait time.

**Issue: Upload succeeds but video doesn't appear**
- Solution: Upload might need form submission or additional trigger.
- Check: Look for "confirm" or "apply" button after upload.

### Step 5: Manual inspection

If automated methods all fail:

1. Open browser manually
2. Navigate to Pikaswaps
3. Open DevTools (F12)
4. Find the upload element:
   ```javascript
   // In browser console
   document.querySelectorAll('input[type="file"]')
   document.querySelectorAll('label')
   ```
5. Note the exact selector and update the script

## Main Script Debug Output

When running the main script, look for these indicators:

**Success indicators:**
```
[DEBUG] Found 1 file input(s)
[DEBUG] Found 5 label(s)
[TRY] Direct input with selector: #modify-region-video
? Successfully uploaded video via direct input
```

**Failure indicators:**
```
[DEBUG] Found 0 file input(s)  ? Page not loaded
[INFO] Method 1 failed: Timeout  ? Elements not ready
[ERROR] All upload methods exhausted  ? Need manual inspection
```

## Quick Fixes to Try

### Fix 1: Increase wait time
In `click_pikaswaps_button()`:
```python
human_sleep(3.0, 4.0)  # Change to (5.0, 7.0)
```

### Fix 2: Wait for specific element
```python
# Add after clicking Pikaswaps
page.wait_for_selector("input[type='file']", timeout=20_000)
```

### Fix 3: Force visible check
```python
# In upload method, add:
page.wait_for_selector("label[for='modify-region-video']", state="visible", timeout=10_000)
```

### Fix 4: Try drag and drop
```python
# Add new method:
def upload_via_drag_drop(page, file_path):
    page.evaluate("""
        const input = document.querySelector('input[type="file"]');
        const dt = new DataTransfer();
        // This simulates drag-drop
        input.dispatchEvent(new Event('change', { bubbles: true }));
    """)
```

## Contact & Support

If all methods fail, please provide:
1. All generated screenshots
2. Complete console output
3. HTML dump from the error message
4. Browser DevTools screenshot of the upload area

This information will help identify the exact issue.
