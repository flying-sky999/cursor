# Installation Guide

## Quick Install

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Verify installation
python -c "import playwright; import pandas; import PIL; print('All dependencies installed!')"
```

## Dependencies

### Required Packages

1. **playwright** (>=1.40.0)
   - Browser automation
   - Core functionality

2. **pandas** (>=2.0.0)
   - Reading Excel task sheets
   - Data processing

3. **openpyxl** (>=3.1.0)
   - Excel file support
   - Required by pandas

4. **Pillow** (>=10.0.0)
   - Screenshot marking
   - Drawing click coordinates
   - **Optional but recommended**

## Step-by-Step Installation

### Step 1: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt
```

Expected output:
```
Collecting playwright>=1.40.0
  Downloading playwright-1.40.0-py3-none-macosx_10_13_x86_64.whl
...
Successfully installed playwright-1.40.0 pandas-2.1.0 openpyxl-3.1.2 Pillow-10.1.0
```

### Step 3: Install Playwright Browsers

```bash
playwright install chromium
```

Expected output:
```
Downloading Chromium 119.0.6045.9 (playwright build v1091)
...
Chromium 119.0.6045.9 downloaded to /Users/.../playwright-1.40.0
```

### Step 4: Verify Installation

```bash
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
python -c "import pandas; print('Pandas OK')"
python -c "from PIL import Image; print('Pillow OK')"
```

All should print "OK".

## Without Pillow

If you can't install Pillow, the script still works:

```bash
# Install without Pillow
pip install playwright pandas openpyxl
playwright install chromium
```

**Impact**: Screenshots saved but without visual markers. You'll see:
```
[WARN] PIL not available, screenshot saved without mark: .../screenshot.png
```

## Troubleshooting

### Issue: playwright command not found

**Solution**:
```bash
# Use python -m instead
python -m playwright install chromium
```

### Issue: Permission denied

**Solution**:
```bash
# Install with --user flag
pip install --user -r requirements.txt
```

### Issue: SSL certificate error

**Solution**:
```bash
# Install with trusted host
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Issue: Pillow installation fails

**Cause**: Missing system libraries

**Solution on Ubuntu/Debian**:
```bash
sudo apt-get install python3-dev libjpeg-dev zlib1g-dev
pip install Pillow
```

**Solution on macOS**:
```bash
brew install libjpeg
pip install Pillow
```

**Solution on Windows**:
- Download Pillow wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pillow
- Install: `pip install Pillow?10.1.0?cp311?cp311?win_amd64.whl`

### Issue: openpyxl not found

**Cause**: Installed in wrong environment

**Solution**:
```bash
# Make sure you're in the virtual environment
which python  # Should show venv path
pip install openpyxl
```

## Upgrade Instructions

### Upgrade All Packages

```bash
pip install --upgrade -r requirements.txt
playwright install chromium --force
```

### Upgrade Specific Package

```bash
pip install --upgrade playwright
pip install --upgrade pandas
pip install --upgrade Pillow
```

## System Requirements

### Minimum Requirements

- **OS**: Windows 10+, macOS 10.13+, or Linux
- **Python**: 3.8+
- **RAM**: 2GB available
- **Disk**: 500MB for dependencies + browser

### Recommended Requirements

- **OS**: macOS 12+, Windows 11, Ubuntu 22.04
- **Python**: 3.10+
- **RAM**: 4GB+ available
- **Disk**: 1GB free space
- **Network**: Stable connection for video upload

## Python Version Check

```bash
python --version
# Should show Python 3.8 or higher

python3 --version
# Try python3 if python doesn't work
```

If Python version is too old:

```bash
# On Ubuntu
sudo apt install python3.10

# On macOS
brew install python@3.10

# On Windows
# Download from https://www.python.org/downloads/
```

## Complete Installation Script

Save this as `install.sh` (macOS/Linux):

```bash
#!/bin/bash

echo "Installing Pika PikaSwap Automation..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install browser
playwright install chromium

# Verify
python -c "from playwright.sync_api import sync_playwright; print('? Playwright installed')"
python -c "import pandas; print('? Pandas installed')"
python -c "from PIL import Image; print('? Pillow installed')"

echo "? Installation complete!"
echo "Run: python pika_pikaswap_automation.py"
```

Make executable and run:
```bash
chmod +x install.sh
./install.sh
```

## Uninstallation

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv

# Or uninstall packages globally
pip uninstall playwright pandas openpyxl Pillow -y
playwright uninstall chromium
```

## Next Steps

After installation:

1. **Configure paths** in `pika_pikaswap_automation.py`
2. **Prepare task sheet** (Excel with video paths and prompts)
3. **Test with one video** first
4. **Run full batch** when ready

See [Usage Examples](USAGE_EXAMPLE.md) for details.
