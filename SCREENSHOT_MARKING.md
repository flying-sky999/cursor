# Screenshot Marking Feature

## Overview

The script now automatically **marks the click coordinates** on debug screenshots, making it easy to verify where the script is clicking.

## How It Works

### Visual Markers

When a screenshot is saved with coordinates, it includes:

```
      (677, 396) ? Coordinate text
         ?
    ----+----    ? Red crosshairs
    |       |
    |   ?   |    ? Red center dot
    |       |
    ----+----
         ?
    ( Red circle ) ? 10px radius outline
```

### Marker Components

1. **Red Circle** - 10px radius outline around the point
2. **Crosshairs** - Red lines extending 20px in each direction
3. **Center Dot** - Small filled circle at exact coordinates
4. **Coordinate Label** - White box with coordinate text "(x, y)"

## Screenshot Examples

### Before Upload (with mark)
```
??????????????????????????????????????????
?  Pika.art - Pikaswaps                 ?
?                                        ?
?  ????????????????????                 ?
?  ?                  ?    (677, 396)   ?
?  ?   [Upload Icon]  ?????????+???     ?
?  ?                  ?        |        ?
?  ?  Upload a video  ?      ? ? Click point
?  ?                  ?        |        ?
?  ????????????????????        +        ?
?                                        ?
?  [Prompt Box]                          ?
?  [Generate Button]                     ?
??????????????????????????????????????????
```

The red circle and crosshairs show exactly where (677, 396) is located!

### After Upload Success (with mark)
Same marking shows the successful click location.

### Upload Failed (with mark)
Shows where the click was attempted but failed.

## Screenshot Files

The script generates:

```
debug_screenshots/
??? before_upload_20231101_153022.png      ? With (677, 396) marked
??? after_upload_success_20231101_153026.png  ? With (677, 396) marked
??? before_upload_20231101_153045.png      ? With (677, 396) marked
??? after_upload_success_20231101_153049.png  ? With (677, 396) marked
??? upload_failed_20231101_153100.png      ? With (677, 396) marked
```

## Console Output

```
[DEBUG] Screenshot saved with mark at (677, 396): .../before_upload_20231101_153022.png
[INFO] Clicking at fixed position: (677, 396)
[INFO] File selected: video.mp4
? Successfully uploaded video via fixed coordinates (677, 396)
[DEBUG] Screenshot saved with mark at (677, 396): .../after_upload_success_20231101_153026.png
```

## Installation

Make sure Pillow is installed:

```bash
pip install Pillow

# Or install all requirements
pip install -r requirements.txt
```

## Without Pillow

If Pillow is not installed, the script will still work but screenshots won't have markers:

```
[WARN] PIL not available, screenshot saved without mark: .../before_upload_20231101_153022.png
```

The script continues normally, just without visual markers.

## Customization

### Change Marker Color

In `save_debug_screenshot()`:

```python
# Change 'red' to any color
draw.ellipse([...], outline='blue', width=3)  # Blue circle
draw.line([...], fill='green', width=2)       # Green crosshairs
draw.text([...], fill='yellow', font=font)    # Yellow text
```

### Change Marker Size

```python
# Larger circle
radius = 15  # Instead of 10

# Longer crosshairs
line_length = 30  # Instead of 20

# Bigger text
font = ImageFont.truetype("...", 20)  # Instead of 16
```

### Change Text Position

```python
# Text above and left
text_x = x - text_width - 15
text_y = y - 25

# Text below
text_x = x + 15
text_y = y + 10
```

## Use Cases

### 1. Verify Click Location

Open `before_upload_*.png` and check:
- ? Is the marker on the upload button?
- ? Is (677, 396) visible and correct?
- ? Is the button ready to click?

### 2. Debug Failed Uploads

If upload fails:
1. Open `upload_failed_*.png`
2. Look at the marker position
3. Check if it's on the right element
4. Verify button is visible

### 3. Adjust Coordinates

If marker is off-target:
1. Note where the marker appears
2. Note where it should be
3. Calculate offset
4. Update coordinates in code:

```python
# If marker is 10px too high
upload_x = 677
upload_y = 396 + 10  # Move down

# If marker is 5px too left
upload_x = 677 + 5  # Move right
upload_y = 396
```

### 4. Compare Before/After

Compare screenshots to verify:
- Upload area changes after click
- Video thumbnail appears
- UI updates correctly

## Troubleshooting

### Issue: Marker not showing

**Cause**: Pillow not installed

**Solution**:
```bash
pip install Pillow
```

### Issue: Font error

**Cause**: Font file not found

**Solution**: The script automatically falls back to default font. No action needed.

### Issue: Marker in wrong position

**Cause**: Coordinates need adjustment

**Solution**:
1. Measure correct position from screenshot
2. Update `upload_x` and `upload_y` in code
3. Run again and verify

### Issue: Can't see marker (red on red)

**Cause**: Background is red

**Solution**: Change marker color to blue or green:
```python
draw.ellipse([...], outline='blue', width=3)
draw.line([...], fill='blue', width=2)
```

## Advanced Features

### Mark Multiple Points

```python
# Mark both upload button and generate button
save_debug_screenshot(page, "both_buttons", mark_point=[(677, 396), (800, 500)])
```

### Add Custom Labels

```python
# Modify save_debug_screenshot to accept label parameter
save_debug_screenshot(page, "before_upload", mark_point=(677, 396), label="Upload Button")
```

### Different Marker Styles

```python
# Square marker instead of circle
draw.rectangle([(x-10, y-10), (x+10, y+10)], outline='red', width=3)

# Star marker
points = [(x, y-15), (x+5, y-5), (x+15, y), (x+5, y+5), (x, y+15), ...]
draw.polygon(points, outline='red')
```

## Technical Details

### Marker Drawing Process

1. **Screenshot capture**
   ```python
   page.screenshot(path=screenshot_path)
   ```

2. **Open image**
   ```python
   img = Image.open(screenshot_path)
   draw = ImageDraw.Draw(img)
   ```

3. **Draw markers**
   ```python
   # Circle
   draw.ellipse([(x-r, y-r), (x+r, y+r)], outline='red', width=3)
   
   # Crosshairs
   draw.line([(x-l, y), (x+l, y)], fill='red', width=2)
   draw.line([(x, y-l), (x, y+l)], fill='red', width=2)
   
   # Center dot
   draw.ellipse([(x-2, y-2), (x+2, y+2)], fill='red')
   ```

4. **Add text**
   ```python
   text = f"({int(x)}, {int(y)})"
   draw.text((text_x, text_y), text, fill='red', font=font)
   ```

5. **Save modified image**
   ```python
   img.save(screenshot_path)
   ```

### Performance

- Marker drawing adds ~0.1-0.2 seconds per screenshot
- Negligible impact on overall execution time
- Can be disabled by not passing `mark_point` parameter

## Examples

### Successful Upload Marker

```
File: before_upload_20231101_153022.png

Visual:
???????????????????????????????????????
?                                     ?
?         Upload Area                 ?
?    ???????????????????             ?
?    ?                 ?  (677, 396) ?
?    ?   ?? Icon       ???????????????
?    ?                 ?        ?    ?
?    ?  Upload Video   ?             ?
?    ???????????????????             ?
?                                     ?
?  Prompt: [____________]             ?
?                                     ?
?         [Generate]                  ?
???????????????????????????????????????

? Marker shows click is on the upload icon
? Coordinates (677, 396) are displayed
? Upload button is visible and clickable
```

### Failed Upload Marker

```
File: upload_failed_20231101_153100.png

Visual:
???????????????????????????????????????
?                                     ?
?         Upload Area                 ?
?    ???????????????????             ?
?    ?                 ?             ?
?    ?   ?? Icon       ?             ?
?    ?                 ?             ?
?    ?  Upload Video   ?             ?
?    ???????????????????             ?
?           (677, 396)                ?
?              ?????????? Marker here ?
?              ?   (wrong position!)  ?
?  Prompt: [____________]             ?
?                                     ?
?         [Generate]                  ?
???????????????????????????????????????

? Marker shows click is below the button
? Coordinates need adjustment
? Solution: Move y coordinate up (y = 396 - 40)
```

## Summary

The screenshot marking feature:

? **Visual verification** - See exactly where the script clicks  
? **Easy debugging** - Quickly identify coordinate issues  
? **No extra steps** - Automatic with every screenshot  
? **Clear feedback** - Coordinates labeled on image  
? **Professional output** - Clean, readable markers  
? **Optional** - Works without Pillow, just no markers  

**Result**: Faster debugging and more confidence in automation!
