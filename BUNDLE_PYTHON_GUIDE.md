# How to Bundle Python with EasyEnv

This guide explains how to include Python and pip in your GitHub repository to avoid download issues for users.

## Why Bundle Python?

**Problem**: Users may experience firewall/antivirus blocks when downloading Python during installation.

**Solution**: Include Python embeddable package (~25 MB) and get-pip.py (~2 MB) directly in the GitHub repo.

## Step-by-Step Instructions

### 1. Download Required Files

Download these files to your local machine:

#### Python 3.13 Embeddable (Windows)
- **URL**: https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip
- **Size**: ~25 MB
- **Save to**: `EasyEnv/ml-sharp/python_embedded/python-3.13.0-embed-amd64.zip`

#### get-pip.py
- **URL**: https://bootstrap.pypa.io/get-pip.py
- **Size**: ~2 MB
- **Save to**: `EasyEnv/ml-sharp/python_embedded/get-pip.py`

### 2. Create Directory Structure

```powershell
# Navigate to your add-on directory
cd D:\GitHub\EasyEnv\EasyEnv\ml-sharp

# Create python_embedded directory
mkdir python_embedded

# Download files into this directory
```

### 3. Download Files (PowerShell)

```powershell
cd D:\GitHub\EasyEnv\EasyEnv\ml-sharp\python_embedded

# Download Python embeddable
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip" -OutFile "python-3.13.0-embed-amd64.zip"

# Download get-pip.py
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "get-pip.py"
```

### 4. Verify Files

Your directory structure should look like:

```
EasyEnv/
├── __init__.py
├── sharp_wrapper.py
├── env_installer.py
├── assets/
└── ml-sharp/
    ├── requirements.txt
    ├── src/
    └── python_embedded/              # NEW
        ├── python-3.13.0-embed-amd64.zip   # ~25 MB
        └── get-pip.py                       # ~2 MB
```

### 5. Update .gitignore (Optional)

The `.gitignore` already excludes the `Env/` folder, but make sure it **does NOT** exclude `python_embedded/`:

```gitignore
# Python environment (will be installed by user)
EasyEnv/ml-sharp/Env/
EasyEnv/ml-sharp/env/

# DO NOT exclude python_embedded/ - we want to commit this!
# EasyEnv/ml-sharp/python_embedded/  ← Make sure this line is NOT present

# ML-Sharp checkpoint (will be downloaded from HuggingFace)
EasyEnv/ml-sharp/*.pt
```

### 6. Commit to GitHub

```powershell
cd D:\GitHub\EasyEnv

# Add the bundled files
git add EasyEnv/ml-sharp/python_embedded/

# Commit
git commit -m "Bundle Python embeddable and get-pip.py to avoid download issues"

# Push to GitHub
git push origin main
```

## How It Works

### Before Bundling:
1. User installs add-on
2. Clicks "Install Environment"
3. **Downloads** Python from python.org (may fail due to firewall)
4. **Downloads** get-pip.py from bootstrap.pypa.io (may fail)
5. Installs packages via pip
6. Downloads checkpoint from HuggingFace

### After Bundling:
1. User installs add-on (includes bundled Python files)
2. Clicks "Install Environment"
3. **Uses bundled** Python (no download, no firewall issues!)
4. **Uses bundled** get-pip.py (no download!)
5. Installs packages via pip (still downloads, but pip is more reliable)
6. Downloads checkpoint from HuggingFace (still downloads, too large to bundle)

## File Size Impact

**GitHub Repository Size:**
- Before bundling: ~5-10 MB
- After bundling: ~32-37 MB
- Still well under GitHub's 100 MB file limit! ✅

**User Download Size:**
- Same as repository size (~32-37 MB)
- Much smaller than if we bundled everything (~2 GB+)

## What Still Gets Downloaded

Even with bundled Python, users will still download:

1. **Python packages** (~2-3 GB)
   - PyTorch, gsplat, numpy, scipy, etc.
   - Installed via pip (more reliable than direct download)
   - Cached in `ml-sharp/Env/Lib/site-packages/`

2. **ML-Sharp checkpoint** (~1.5 GB)
   - Downloaded from HuggingFace
   - Too large to bundle in GitHub
   - Cached in `ml-sharp/sharp_2572gikvuh.pt`

## Benefits

✅ **No firewall issues** - Python files are already present
✅ **Faster installation** - No waiting for Python download
✅ **More reliable** - Fewer points of failure
✅ **Offline-friendly** - Less internet required
✅ **Still small repo** - Only ~30 MB increase

## Testing

After bundling, test the installation:

1. Delete your `ml-sharp/Env/` folder
2. Restart Blender and load the add-on
3. Click "Install Environment"
4. You should see: "Using bundled Python 3.13 (no download needed)..."
5. Installation should proceed without downloading Python

## Troubleshooting

### Files not found during installation

**Check file paths:**
```powershell
# Verify files exist
ls "D:\GitHub\EasyEnv\EasyEnv\ml-sharp\python_embedded\"

# Should show:
# python-3.13.0-embed-amd64.zip
# get-pip.py
```

### GitHub won't accept large files

**File size limits:**
- GitHub warns at 50 MB
- GitHub blocks at 100 MB
- Our files are ~27 MB total - well within limits!

If you get an error, check file size:
```powershell
ls -l "D:\GitHub\EasyEnv\EasyEnv\ml-sharp\python_embedded\"
```

### Wrong Python version

Make sure you download **Python 3.13** embeddable for **Windows x64**:
- ✅ `python-3.13.0-embed-amd64.zip`
- ❌ `python-3.12.x-embed-amd64.zip` (wrong version)
- ❌ `python-3.13.0-embed-win32.zip` (wrong architecture)
- ❌ `python-3.13.0-amd64.exe` (wrong format - need embeddable zip)

## For macOS/Linux Support (Future)

Currently only Windows is bundled. For cross-platform support:

```
ml-sharp/python_embedded/
├── windows/
│   ├── python-3.13.0-embed-amd64.zip
│   └── get-pip.py
├── macos/
│   └── (future)
└── linux/
    └── (future)
```

Update `env_installer.py` to detect platform and use appropriate bundle.

## Alternative: Git LFS (Not Recommended)

You could use Git Large File Storage, but it's unnecessary for files this small:
- Git LFS is for files >50 MB
- Our files are ~27 MB total
- Regular git works fine!

## Summary

By bundling Python and get-pip.py (~27 MB total), you eliminate the most common installation failure point while keeping your GitHub repo small and manageable. Users will still download packages and the checkpoint via pip/HuggingFace, which are more reliable download sources.
