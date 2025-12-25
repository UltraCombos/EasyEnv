# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EasyEnv** is a Blender add-on that generates 3D Gaussian Splatting environments from single images using ML-Sharp (Apple's monocular view synthesis model). The add-on integrates ML-Sharp's inference capabilities directly into Blender's UI, automating the workflow from image input to rendered 3D scene.

### Key Architecture Principle

**Subprocess-Based Isolation**: The add-on uses subprocess to invoke ML-Sharp's embedded Python environment (`ml-sharp/Env/python.exe`), keeping Blender's Python completely untouched. This avoids dependency conflicts and makes distribution simple.

```
Blender Python → subprocess → ml-sharp/Env/python.exe → sharp CLI → PLY output → Auto-import to Blender
```

## Repository Structure

```
EasyEnv_1.0.0/
├── __init__.py                 # Main Blender add-on (operators, UI, geometry nodes)
├── sharp_wrapper.py            # Subprocess wrapper for ml-sharp CLI
├── assets/                     # Blender assets
│   └── 3DGS Render APPEND V4.blend  # Geometry node groups and materials
└── ml-sharp/                   # ML-Sharp package (Apple's research project)
    ├── Env/                    # Embedded Python environment with all dependencies
    │   ├── python.exe          # Python 3.13 interpreter
    │   └── Lib/site-packages/  # PyTorch, gsplat, timm, sharp package, etc.
    ├── src/sharp/              # Sharp source code (model, CLI, utils)
    └── Output/                 # Generated PLY files destination
```

## Core Components

### 1. __init__.py (Main Add-on)

**Blender Operators**:
- `SNA_OT_Generate_Gaussians_From_Image`: Generate 3DGS from image via ML-Sharp
- `SNA_OT_Dgs_Render_Import_Ply_E0A3A`: Import PLY files with 3DGS attributes
- `SNA_OT_Dgs_Render_Align_Active_To_View_30B13`: Update Gaussian splat camera alignment

**Key Functions**:
- `sna_append_and_add_geo_nodes_function_execute_6BCD7()`: Appends geometry node groups from `assets/3DGS Render APPEND V4.blend` and applies them as modifiers
- `sna_update_camera_single_time_9EF18()`: Updates geometry node sockets with camera view/projection matrices and window dimensions

**3DGS Import Pipeline** (used by both operators):
1. Import PLY file using `bpy.ops.wm.ply_import()`
2. Validate required attributes: `f_dc_0-2`, `opacity`, `scale_0-2`, `rot_0-3`
3. Convert spherical harmonics to RGBA colors using SH_0 constant
4. Create `Col` and `KIRI_3DGS_Paint` color attributes
5. Apply 4 geometry node modifiers:
   - `KIRI_3DGS_Render_GN`: Main rendering with camera matrices
   - `KIRI_3DGS_Sorter_GN`: Depth sorting for alpha blending
   - `KIRI_3DGS_Adjust_Colour_And_Material`: Color adjustments
   - `KIRI_3DGS_Write F_DC_And_Merge`: Write back color data
6. Assign `KIRI_3DGS_Render_Material` from library

### 2. sharp_wrapper.py (ML-Sharp Integration)

**Purpose**: Provides Python API to call ML-Sharp via subprocess, avoiding direct imports that would pollute Blender's Python environment.

**Key Functions**:
- `predict_gaussians_from_image()`: Runs ML-Sharp inference by executing `ml-sharp/Env/python.exe -m sharp.cli predict`
- `check_mlsharp_environment()`: Validates that ml-sharp's Python environment exists and works
- `verify_sharp_package()`: Tests if sharp package is importable in ml-sharp's environment

**Important**: The wrapper sets `PYTHONPATH=ml-sharp/src` before subprocess execution so the `sharp` package can be found by Python's module system.

### 3. ML-Sharp Integration

ML-Sharp is Apple's research project for monocular view synthesis. The add-on uses it as an embedded dependency:

- **Model**: Downloads `sharp_2572gikvuh.pt` (~1.5GB) on first run or uses bundled checkpoint
- **Inference**: Generates 3D Gaussian splat PLY files from single images
- **CLI**: `python -m sharp.cli predict -i <image> -o <output> [-c <checkpoint>] [--device cpu|cuda|mps]`
- **Output**: Standard 3DGS PLY format with spherical harmonics attributes

## Development Commands

### Testing ML-Sharp Integration (Outside Blender)

```powershell
# From repository root
cd EasyEnv_1.0.0

# Verify ml-sharp environment
.\setup_mlsharp.ps1

# Test sharp_wrapper.py with Blender's Python
& "C:\Program Files\Blender Foundation\Blender 4.3\4.3\python\bin\python.exe" test_mlsharp.py

# Test ML-Sharp CLI directly
cd ml-sharp
.\Env\python.exe -m sharp.cli predict -i Input/test.png -o Output --device cpu
```

### Installing/Testing Add-on in Blender

1. **Edit → Preferences → Add-ons → Install**
2. Select `EasyEnv_1.0.0/__init__.py`
3. Enable **EasyEnv** checkbox
4. Open 3D Viewport → Press `N` → **Easy Env** tab
5. Test "Generate from Image" with sample image

### Debugging

- **Enable Blender Console**: `Window → Toggle System Console` (Windows)
- **Verbose Logging**: Check "Verbose Logging" in operator dialog
- **Test Subprocess**: Run `sharp_wrapper.py` functions directly with Blender's Python
- **Validate Environment**: `sharp_wrapper.check_mlsharp_environment()` returns status dict

## Important Technical Details

### Camera Matrix System

The 3DGS rendering geometry nodes require camera matrices to properly orient Gaussian splats. These are updated via geometry node sockets:

- **View Matrix** (4x4): Sockets 2-17 (row-major order)
- **Projection Matrix** (4x4): Sockets 18-33 (row-major order)
- **Window Dimensions**: Sockets 34-35 (width, height)

Camera updates happen via:
- Manual: "Update Active To View" button
- Automatic: "Enable Active Camera Updates" property with timer callback

### 3DGS Attribute Requirements

Valid 3DGS PLY files must contain these float attributes per point:
- `f_dc_0`, `f_dc_1`, `f_dc_2`: 0th order spherical harmonics (RGB)
- `opacity`: Gaussian opacity (pre-sigmoid)
- `scale_0`, `scale_1`, `scale_2`: Gaussian ellipsoid scale
- `rot_0`, `rot_1`, `rot_2`, `rot_3`: Quaternion rotation

Higher-order SH coefficients (`f_rest_*`) are optional but not used by this minimal version.

### Spherical Harmonics to RGB Conversion

```python
SH_0 = 0.28209479177387814  # sqrt(1/(4*pi))
R = clamp(f_dc_0 * SH_0 + 0.5, 0.0, 1.0)
G = clamp(f_dc_1 * SH_0 + 0.5, 0.0, 1.0)
B = clamp(f_dc_2 * SH_0 + 0.5, 0.0, 1.0)
A = clamp(sigmoid(opacity), 0.0, 1.0)  # sigmoid(x) = 1/(1+exp(-x))
```

### Subprocess Environment Setup

When calling ML-Sharp, the wrapper modifies the environment:

```python
env = os.environ.copy()
mlsharp_src = "ml-sharp/src"
env['PYTHONPATH'] = mlsharp_src + os.pathsep + env.get('PYTHONPATH', '')
```

This ensures `import sharp` works in ml-sharp's Python without installing the package.

### Cross-Platform Python Executable Detection

```python
# Windows
MLSHARP_PYTHON = "ml-sharp/Env/python.exe"

# macOS/Linux
MLSHARP_PYTHON = "ml-sharp/Env/bin/python"
```

## Common Development Tasks

### Modifying ML-Sharp CLI Arguments

Edit `sharp_wrapper.py` `predict_gaussians_from_image()`:

```python
cmd = [
    str(MLSHARP_PYTHON),
    "-m", "sharp.cli",
    "predict",
    "-i", str(image_path),
    "-o", str(output_path),
    "--device", device,
    "--your-custom-arg", "value"
]
```

### Adding Post-Import Transformations

Edit `__init__.py` in `SNA_OT_Generate_Gaussians_From_Image.execute()` after PLY import:

```python
# After: obj = imported_objects[0]
obj.scale = (2.0, 2.0, 2.0)
obj.location = (0, 0, 1)
```

### Changing Geometry Node Setup

Edit `__init__.py` function `sna_append_and_add_geo_nodes_function_execute_6BCD7()` or modify the node groups in `assets/3DGS Render APPEND V4.blend`.

### Using Custom Model Checkpoints

Place checkpoint file in `ml-sharp/` directory and it will be auto-detected by name pattern `sharp_*.pt`, or modify operator code to specify explicit path.

## Error Handling Patterns

### ML-Sharp Environment Not Found

```python
env_status = sharp_wrapper.check_mlsharp_environment()
if not env_status['available']:
    self.report({'ERROR'}, env_status['message'])
    return {'CANCELLED'}
```

### Subprocess Execution Failure

The wrapper raises `RuntimeError` with detailed message including:
- Exit code
- Full command line
- stdout and stderr output

Catch in operator:
```python
try:
    output_ply = sharp_wrapper.predict_gaussians_from_image(...)
except RuntimeError as e:
    self.report({'ERROR'}, f"ML-Sharp failed: {str(e)}")
    return {'CANCELLED'}
```

### Missing 3DGS Attributes

```python
required_attributes = ['f_dc_0', 'f_dc_1', 'f_dc_2', 'opacity',
                       'scale_0', 'scale_1', 'scale_2',
                       'rot_0', 'rot_1', 'rot_2', 'rot_3']
missing_attrs = [attr for attr in required_attributes if attr not in mesh.attributes]
if missing_attrs:
    self.report({'ERROR'}, f"Missing attributes: {', '.join(missing_attrs)}")
    return {'CANCELLED'}
```

## Dependencies

### Blender Add-on Dependencies
- Blender 4.3.0+ (for `bpy.ops.wm.ply_import` support)
- NumPy (bundled with Blender)
- `assets/3DGS Render APPEND V4.blend` (geometry nodes and materials)

### ML-Sharp Environment Dependencies
All contained in `ml-sharp/Env/`:
- Python 3.13
- PyTorch 2.8.0
- gsplat 1.5.3
- timm 1.0.20 (image models)
- sharp package (Apple's research code)
- scipy, matplotlib, imageio, pillow-heif, plyfile

See `ml-sharp/requirements.txt` for full list.

## Known Limitations

- ML-Sharp rendering (`sharp render`) requires CUDA GPU - not used by this add-on
- Only 0th order spherical harmonics are processed (higher orders ignored)
- Camera updates only work in viewport mode, not in camera view
- Geometry node modifiers are hardcoded to specific names from KIRI Engine
- Windows-centric paths (though cross-platform detection exists)

## Related Documentation Files

- `QUICKSTART.md`: Quick reference for users
- `INTEGRATION_GUIDE.md`: Detailed setup and troubleshooting
- `IMPLEMENTATION_COMPLETE.md`: Implementation notes
- `ml-sharp/README.md`: ML-Sharp original documentation
- `blender_manifest.toml`: Blender 4.2+ extension manifest
