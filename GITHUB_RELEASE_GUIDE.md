# GitHub Release Guide for EasyEnv

This guide explains how to prepare and release the EasyEnv Blender add-on on GitHub while staying under the 100MB file size limit.

## Overview

The add-on now features an **"Install Environment" button** that automatically downloads and installs:
1. Portable Python 3.13 (~25MB)
2. All required Python packages via pip (PyTorch, gsplat, etc.)
3. ML-Sharp checkpoint file from HuggingFace (~1.5GB)

This approach keeps the GitHub repository small while ensuring users get the exact same environment.

## What to Include in GitHub Repository

### Files to INCLUDE in your release:

```
EasyEnv/
├── __init__.py                    # Main add-on file
├── sharp_wrapper.py               # ML-Sharp subprocess wrapper
├── env_installer.py               # NEW: Environment installer module
├── assets/
│   ├── 3DGS Render APPEND V4.blend
│   └── eye.svg
└── ml-sharp/
    ├── requirements.txt           # Python package dependencies
    └── src/                       # ML-Sharp source code
        └── sharp/
            ├── __init__.py
            ├── cli.py
            ├── model.py
            └── ... (all source files)
```

### Files to EXCLUDE from GitHub:

```
ml-sharp/
├── Env/                           # Will be downloaded by installer
├── Output/                        # Generated files
└── sharp_2572gikvuh.pt           # Will be downloaded from HuggingFace
```

**Total GitHub repo size: ~5-10 MB** (just your code + ml-sharp source)

## Creating .gitignore

Create or update `.gitignore` in your repository root:

```gitignore
# Python environment (will be installed by user)
EasyEnv/ml-sharp/Env/
EasyEnv/ml-sharp/env/

# ML-Sharp checkpoint (will be downloaded)
EasyEnv/ml-sharp/*.pt
EasyEnv/ml-sharp/*.pth

# Output files
EasyEnv/ml-sharp/Output/
EasyEnv/ml-sharp/Input/

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db
```

## Release Steps

### 1. Prepare Your Repository

```powershell
# Navigate to your repo
cd D:\GitHub\EasyEnv

# Add .gitignore
# (Create the file with content above)

# Remove Env folder from tracking if it exists
git rm -r --cached EasyEnv/ml-sharp/Env/

# Remove checkpoint from tracking if it exists
git rm --cached EasyEnv/ml-sharp/*.pt

# Add your changes
git add .

# Commit
git commit -m "Add auto-installer and prepare for GitHub release"

# Push to GitHub
git push origin main
```

### 2. Create a GitHub Release

1. Go to your GitHub repository
2. Click **"Releases"** → **"Create a new release"**
3. Tag version: `v1.0.0`
4. Release title: `EasyEnv v1.0.0 - Blender 3D Environment Generator`
5. Description:

```markdown
## EasyEnv - Generate 3D Gaussian Splatting Environments from Single Images

EasyEnv is a Blender add-on that uses Apple's ML-Sharp to generate 3D Gaussian Splatting environments from single images.

### ✨ Features
- Generate 3D environments from any image
- Uses Apple's ML-Sharp monocular view synthesis
- Built-in 3D Gaussian Splatting renderer
- GPU-accelerated inference (CUDA, CPU, MPS support)

### 📦 Installation

1. **Download** the add-on zip from this release
2. **Install** in Blender: Edit → Preferences → Add-ons → Install
3. **Enable** the "EasyEnv" add-on
4. **Install Environment**: In the 3D Viewport sidebar (press N), go to the "Easy Env" tab
5. Click **"Install Environment"** button (first-time setup, ~10-15 minutes)
   - Downloads Python 3.13
   - Installs PyTorch and dependencies
   - Downloads ML-Sharp checkpoint (~1.5GB)

### 🚀 Usage

1. Open the "Easy Env" panel in 3D Viewport sidebar (press N)
2. Select device (GPU recommended)
3. Click "Generate PLY from Image"
4. Choose your input image
5. Wait for processing (1-5 minutes depending on hardware)
6. The 3D Gaussian splat will appear in your scene

### ⚙️ Requirements

- Blender 4.3.0 or later
- Windows (automatic installation)
- macOS/Linux (manual Python setup required - see documentation)
- 3-4 GB free disk space for environment
- Optional: NVIDIA GPU with CUDA for faster inference

### 📝 Notes

- First-time setup requires internet connection to download dependencies
- The "Install Environment" button only needs to be clicked once
- Checkpoint file is cached after first download
- Works offline after initial setup

### 🐛 Known Issues

- Automatic installation currently Windows-only
- macOS/Linux users must manually install Python 3.13 and run `pip install -r requirements.txt`
```

6. **Upload assets**: Create a zip file of the EasyEnv folder (without Env/ and checkpoints)

```powershell
# Create release zip
Compress-Archive -Path "D:\GitHub\EasyEnv\EasyEnv" -DestinationPath "D:\GitHub\EasyEnv\EasyEnv-v1.0.0.zip"
```

7. Attach `EasyEnv-v1.0.0.zip` to the release
8. Click **"Publish release"**

## User Installation Flow

### What Users Will Do:

1. **Download** `EasyEnv-v1.0.0.zip` from GitHub Releases
2. **Install** in Blender:
   - Edit → Preferences → Add-ons → Install
   - Select the downloaded zip
   - Enable "EasyEnv" checkbox
3. **First-time setup**:
   - Open 3D Viewport → Press `N` → Click "Easy Env" tab
   - See "Environment Setup" section showing installation status
   - Click **"Install Environment"** button
   - Wait 10-15 minutes while it downloads and installs everything

### What the Installer Does Automatically:

1. Downloads Python 3.13 embeddable package (~25MB)
2. Extracts Python to `ml-sharp/Env/`
3. Installs pip
4. Runs `pip install -r requirements.txt` (downloads PyTorch, gsplat, etc.)
5. Downloads checkpoint from HuggingFace (~1.5GB)
6. Shows completion message

After installation, the environment is fully self-contained and works offline.

## Updating the Add-on

When you release updates, users can:

1. Download new version from GitHub
2. Reinstall in Blender (overwrites old version)
3. The `ml-sharp/Env/` folder is preserved, so no need to reinstall environment

## Testing Before Release

1. **Clean test**: Delete `ml-sharp/Env/` and checkpoint file
2. Load add-on in Blender
3. Click "Install Environment"
4. Verify it downloads everything correctly
5. Test generating a 3DGS from an image

## Alternative: Manual Installation Instructions (macOS/Linux)

For macOS/Linux users, provide these manual steps in your README:

```bash
# Install Python 3.13 (using your system's package manager)

# Navigate to add-on directory
cd ~/.config/blender/4.3/scripts/addons/EasyEnv/ml-sharp

# Create virtual environment
python3.13 -m venv Env

# Activate environment
source Env/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Checkpoint will auto-download on first use
```

## Repository Size Comparison

### Before (with Env folder):
- **Size**: ~3-4 GB
- **Cannot upload to GitHub** (over 100MB limit for many files)
- **Slow clones/downloads**

### After (with auto-installer):
- **Size**: ~5-10 MB
- **Fast clones/downloads**
- **Users download dependencies on-demand**
- **Same exact environment for everyone**

## Benefits of This Approach

✅ **Small GitHub repo** - Only source code
✅ **No Git LFS needed** - Standard GitHub works fine
✅ **Reproducible** - requirements.txt ensures exact versions
✅ **Easy updates** - Change requirements.txt, users reinstall
✅ **Bandwidth efficient** - Users only download what they need
✅ **Works offline after setup** - All files cached locally

## Troubleshooting

If users report installation issues:

1. **Check console** - Window → Toggle System Console (Windows)
2. **Firewall/antivirus** - May block downloads
3. **Disk space** - Need 3-4 GB free
4. **Network issues** - Retry installation
5. **Manual install** - Provide fallback instructions

## Future Improvements

Consider adding:
- Progress bar in Blender UI (currently console-only)
- Verify checksums of downloaded files
- Retry logic for failed downloads
- Support for proxies
- macOS/Linux auto-installers
