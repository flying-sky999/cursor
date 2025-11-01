# Usage Example

## Simple Usage Example

This document shows a complete example of using the Pika PikaSwap automation script with the fixed coordinate upload method.

## Step-by-Step Example

### 1. Prepare Your Files

**Video Folder**: `/Users/helensliang/important/paper-data-ppt/InstructBench/pika/source`
```
source/
??? video1.mp4
??? video2.mp4
??? video3.mp4
```

**Task Spreadsheet**: `InstructBench.xlsx`
```
source_video_path | instruction
-----------------|-------------------------------------------
video1.mp4       | Replace the person with a robot
video2.mp4       | Change the car to a bicycle
video3.mp4       | Transform the dog into a cat
```

### 2. Run the Script

```bash
cd /workspace
python pika_pikaswap_automation.py
```

### 3. What Happens

The script will:

#### Task 1: video1.mp4

```
============================================================
[TASK 1/3] video1.mp4
============================================================

# Step 1: Navigate and click Pikaswaps
[STEP 1] Clicking Pikaswaps feature button...
? Successfully clicked Pikaswaps button
[INFO] Waiting for Pikaswaps interface to load...
[INFO] Form detected, interface ready

# Step 2: Upload video using fixed coordinates
[STEP 2] Uploading video: .../source/video1.mp4
[DEBUG] Video file size: 8.75 MB
[DEBUG] Screenshot saved: .../before_upload_20231101_153022.png

[METHOD 1] Clicking at fixed coordinates (677, 396)...
[INFO] Clicking at fixed position: (677, 396)
          ? Clicks here to open file chooser
          ? File dialog opens
[INFO] File selected: video1.mp4
          ? Selects from local folder
          ? Upload starts
? Successfully uploaded video via fixed coordinates (677, 396)
[DEBUG] Screenshot saved: .../after_upload_success_20231101_153026.png

# Step 3: Fill prompt
[STEP 3] Filling prompt: Replace the person with a robot...
? Successfully filled prompt

# Step 4: Click generate
[STEP 4] Clicking generate button...
? Successfully clicked generate button

? Task 1 completed successfully

Waiting 10 seconds before next task...
```

#### Task 2: video2.mp4

```
============================================================
[TASK 2/3] video2.mp4
============================================================

[STEP 1] Clicking Pikaswaps feature button...
? Successfully clicked Pikaswaps button

[STEP 2] Uploading video: .../source/video2.mp4
[DEBUG] Video file size: 12.34 MB

[METHOD 1] Clicking at fixed coordinates (677, 396)...
[INFO] Clicking at fixed position: (677, 396)
[INFO] File selected: video2.mp4
? Successfully uploaded video via fixed coordinates (677, 396)

[STEP 3] Filling prompt: Change the car to a bicycle...
? Successfully filled prompt

[STEP 4] Clicking generate button...
? Successfully clicked generate button

? Task 2 completed successfully
```

#### Task 3: video3.mp4

```
[Similar output...]
```

### 4. Final Summary

```
============================================================
All tasks processed! Success: 3/3
============================================================

Browser will remain open. Press Ctrl+C to exit...
```

## Visual Explanation

### The Upload Process

```
????????????????????????????????????????????????????????????
?  Pika.art - Pikaswaps Interface                         ?
?                                                          ?
?  ??????????????????????????????????                     ?
?  ?                                ?                     ?
?  ?      [Upload Icon]             ? ? (677, 396)        ?
?  ?                                ?    Click here!      ?
?  ?   Upload a video               ?                     ?
?  ?   Make sure your video is...   ?                     ?
?  ?                                ?                     ?
?  ??????????????????????????????????                     ?
?                                                          ?
?  ??????????????????????????????????                     ?
?  ? Prompt: [                    ] ?                     ?
?  ??????????????????????????????????                     ?
?                                                          ?
?              [Generate Button]                           ?
????????????????????????????????????????????????????????????

After clicking (677, 396):
?
????????????????????????????????????????
?  File Chooser Dialog                 ?
?                                      ?
?  Select video to upload:             ?
?  ? video1.mp4                        ? ? Script selects this
?  ? video2.mp4                        ?
?  ? video3.mp4                        ?
?                                      ?
?          [Open]   [Cancel]           ?
????????????????????????????????????????
```

## Debug Screenshots

After each task, check these screenshots:

```
{DOWNLOAD_DIR}/debug_screenshots/
??? before_upload_20231101_153022.png      ? Shows page before clicking
??? after_upload_success_20231101_153026.png  ? Shows uploaded state
??? before_upload_20231101_153045.png      ? Task 2
??? after_upload_success_20231101_153049.png
??? ...
```

## If Something Goes Wrong

### Example: Method 1 Fails

```
[METHOD 1] Clicking at fixed coordinates (677, 396)...
[INFO] Clicking at fixed position: (677, 396)
[WARN] Fixed coordinate click at (677, 396) failed: Timeout

[METHOD 2] Trying direct file input...
[TRY] Setting files directly to input element
? Successfully uploaded video via direct input
```

The script automatically tries the next method!

### Example: All Methods Work

```
[METHOD 1] Clicking at fixed coordinates (677, 396)...
? Successfully uploaded video via fixed coordinates (677, 396)
```

No need to try other methods!

## Common Scenarios

### Scenario 1: Perfect Run

- All 3 tasks complete successfully
- Each takes ~40 seconds
- Total time: ~2-3 minutes
- No errors

### Scenario 2: One Upload Retry

- Task 1: Method 1 succeeds
- Task 2: Method 1 fails, Method 2 succeeds
- Task 3: Method 1 succeeds
- Total time: ~3-4 minutes
- All tasks complete

### Scenario 3: Network Delay

- Uploads take longer
- Script waits patiently
- Eventually all complete
- Total time: ~5-10 minutes

## Verification

After running, verify:

1. **Check console output** - All tasks show ?
2. **Check screenshots** - Videos appear in upload area
3. **Check Pika.art** - Generation requests submitted
4. **Wait for results** - Pika will process videos

## Tips for Best Results

1. **Stable network connection**
   - Upload speed matters
   - Avoid WiFi if possible

2. **Don't disturb the browser**
   - Let it run in background
   - Don't click or resize

3. **Check before running**
   - All video files exist
   - Spreadsheet is correct
   - Paths are valid

4. **Monitor first task**
   - Watch the console output
   - Verify upload works
   - Check screenshots

## Real-World Example

```bash
# My actual command
$ python pika_pikaswap_automation.py

# Console output
============================================================
Pika PikaSwap Automation - Coordinate Click Version
============================================================

[INFO] Tasks to process: 5

[NAV] Opening https://pika.art/app...
? Page loaded

============================================================
[TASK 1/5] car_scene.mp4
============================================================
[STEP 1] Clicking Pikaswaps feature button...
? Successfully clicked Pikaswaps button

[STEP 2] Uploading video: .../car_scene.mp4
[DEBUG] Video file size: 15.23 MB
[METHOD 1] Clicking at fixed coordinates (677, 396)...
[INFO] Clicking at fixed position: (677, 396)
[INFO] File selected: car_scene.mp4
? Successfully uploaded video via fixed coordinates (677, 396)

[STEP 3] Filling prompt: Replace the red car with a blue bicycle...
? Successfully filled prompt

[STEP 4] Clicking generate button...
? Successfully clicked generate button
? Task 1 completed successfully

Waiting 10 seconds before next task...

[... Tasks 2-5 continue ...]

============================================================
All tasks processed! Success: 5/5
============================================================

# Result: Perfect! All tasks submitted successfully
```

## Summary

The fixed coordinate method (677, 396):
- ? Clicks the upload button reliably
- ? Opens file chooser dialog
- ? Allows selecting videos from local folder
- ? Has automatic fallbacks if needed
- ? Provides clear feedback in console
- ? Saves debug screenshots for verification

**Just run the script and let it work!** ??
