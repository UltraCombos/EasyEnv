"""
ML-Sharp wrapper for Blender integration.
This module uses ml-sharp's embedded Python environment via subprocess.
This avoids modifying Blender's Python installation.
"""

import os
import sys
import subprocess
from pathlib import Path

ADDON_DIR = Path(__file__).parent
MLSHARP_DIR = ADDON_DIR / "ml-sharp"
MLSHARP_ENV_DIR = MLSHARP_DIR / "Env"

# Detect ml-sharp's embedded Python executable
if os.name == 'nt':  # Windows
    MLSHARP_PYTHON = MLSHARP_ENV_DIR / "python.exe"
else:  # macOS/Linux
    MLSHARP_PYTHON = MLSHARP_ENV_DIR / "bin" / "python"


def predict_gaussians_from_image(
    image_path: Path,
    output_path: Path,
    checkpoint_path: Path = None,
    device: str = "default",
    verbose: bool = False
) -> Path:
    """
    Generate Gaussian Splatting PLY file from a single image.
    Uses ml-sharp's embedded Python environment via subprocess.
    
    Args:
        image_path: Path to input image
        output_path: Directory to save output PLY file
        checkpoint_path: Path to model checkpoint (optional, will download if not provided)
        device: Device to use ('cpu', 'cuda', 'mps', or 'default')
        verbose: Enable verbose logging
    
    Returns:
        Path to generated PLY file
    
    Raises:
        FileNotFoundError: If input image or ml-sharp Python not found
        RuntimeError: If prediction fails
    """
    
    # Validate ml-sharp Python exists
    if not MLSHARP_PYTHON.exists():
        raise FileNotFoundError(
            f"ML-Sharp embedded Python not found at: {MLSHARP_PYTHON}\n"
            f"Expected location: {MLSHARP_ENV_DIR}\n"
            "Please ensure ml-sharp's Env folder is present."
        )
    
    # Validate input
    if not image_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")
    
    # Create output directory
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Check for checkpoint
    if checkpoint_path is None:
        bundled_checkpoint = MLSHARP_DIR / "sharp_2572gikvuh.pt"
        if bundled_checkpoint.exists():
            checkpoint_path = bundled_checkpoint
    
    # Build command
    # Note: Windows embeddable Python often ignores PYTHONPATH, so we need to
    # modify sys.path at runtime using a wrapper script approach
    mlsharp_src = str(MLSHARP_DIR / "src")

    # Create inline Python code that adds src to path and runs sharp.cli
    python_code = f"""
import sys
sys.path.insert(0, {repr(mlsharp_src)})
from sharp.cli import main_cli
sys.exit(main_cli())
"""

    # Build command with arguments for sharp CLI
    cmd = [
        str(MLSHARP_PYTHON),
        "-c", python_code,
        "predict",
        "-i", str(image_path),
        "-o", str(output_path),
        "--device", device
    ]

    if checkpoint_path:
        cmd.extend(["-c", str(checkpoint_path)])

    if verbose:
        cmd.append("-v")

    # Still set PYTHONPATH as backup (works on some systems)
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = mlsharp_src + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = mlsharp_src
    
    # Run ml-sharp prediction
    print(f"Running ML-Sharp with embedded Python: {MLSHARP_PYTHON.name}")
    print(f"Processing: {image_path.name}")
    print(f"Output directory: {output_path}")
    if verbose:
        print(f"Command: {' '.join(cmd)}")
        print(f"PYTHONPATH: {env['PYTHONPATH']}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=str(MLSHARP_DIR),
            env=env  # Pass the modified environment
        )
        
        if verbose:
            print("=== ML-Sharp Output ===")
            print(result.stdout)
        
        # Find generated PLY file
        output_ply = output_path / f"{image_path.stem}.ply"

        if output_ply.exists():
            print(f"Successfully generated: {output_ply.name}")

            # Convert to industry-standard PLY format for compatibility
            # with Houdini, SuperSplat, and other 3DGS software
            print("Converting to industry-standard PLY format...")
            standardize_ply_format(output_ply, verbose=verbose)
            print(f"PLY format standardized: {output_ply.name}")

            return output_ply
        else:
            raise RuntimeError(f"Expected output PLY not found: {output_ply}")
            
    except subprocess.CalledProcessError as e:
        error_msg = f"ML-Sharp prediction failed with exit code {e.returncode}\n"
        error_msg += f"Command: {' '.join(cmd)}\n"
        if e.stdout:
            error_msg += f"Output: {e.stdout}\n"
        if e.stderr:
            error_msg += f"Error: {e.stderr}"
        raise RuntimeError(error_msg)
    except Exception as e:
        raise RuntimeError(f"Unexpected error during prediction: {e}")


def check_mlsharp_environment():
    """
    Check if ml-sharp embedded Python environment is properly set up.
    
    Returns:
        dict: Status information with keys 'available', 'python_path', 'message'
    """
    status = {
        'available': False,
        'python_path': str(MLSHARP_PYTHON),
        'message': ''
    }
    
    if not MLSHARP_PYTHON.exists():
        status['message'] = f"ML-Sharp Python not found at: {MLSHARP_PYTHON}"
        return status
    
    # Try to run a simple command to verify it works
    try:
        result = subprocess.run(
            [str(MLSHARP_PYTHON), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            status['available'] = True
            status['message'] = f"ML-Sharp environment ready: {result.stdout.strip()}"
        else:
            status['message'] = "ML-Sharp Python found but not responding correctly"
            
    except Exception as e:
        status['message'] = f"Error checking ML-Sharp environment: {e}"
    
    return status


def verify_sharp_package():
    """
    Verify that sharp package is available in ml-sharp environment.

    Returns:
        bool: True if sharp package is available
    """
    if not MLSHARP_PYTHON.exists():
        return False

    try:
        result = subprocess.run(
            [str(MLSHARP_PYTHON), "-c", "import sharp; print(sharp.__file__)"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False

def standardize_ply_format(ply_path: Path, verbose: bool = False) -> bool:
    """
    Convert ML-Sharp PLY format to industry-standard 3DGS PLY format.

    This function:
    1. Removes non-standard elements (extrinsic, intrinsic, etc.)
    2. Reorders properties to standard order
    3. Converts quaternions from WXYZ (ML-Sharp) to XYZW (industry standard)
    4. Filters out any NaN/Infinity values

    Args:
        ply_path: Path to PLY file to standardize (modified in-place)
        verbose: Enable verbose logging

    Returns:
        bool: True if successful

    Raises:
        RuntimeError: If standardization fails
    """
    if not MLSHARP_PYTHON.exists():
        raise FileNotFoundError(f"ML-Sharp Python not found: {MLSHARP_PYTHON}")

    if not ply_path.exists():
        raise FileNotFoundError(f"PLY file not found: {ply_path}")

    # Python code to run in ml-sharp environment (has plyfile and numpy)
    python_code = '''
import sys
import numpy as np
from plyfile import PlyData, PlyElement

def save_as_splat(data, output_path):
    """Save to 32-byte per splat binary format for Unity/Web."""
    with open(output_path, 'wb') as f:
        for row in data:
            # 1. Position (x, y, z) - 12 bytes
            f.write(np.float32(row['x']).tobytes())
            f.write(np.float32(row['y']).tobytes())
            f.write(np.float32(row['z']).tobytes())
            
            # 2. Scale (exp conversion) - 12 bytes
            f.write(np.exp(np.float32(row['scale_0'])).tobytes())
            f.write(np.exp(np.float32(row['scale_1'])).tobytes())
            f.write(np.exp(np.float32(row['scale_2'])).tobytes())
            
            # 3. Color & Opacity (RGBA) - 4 bytes
            SH_C0 = 0.28209479177387814
            r = np.clip((0.5 + SH_C0 * row['f_dc_0']) * 255, 0, 255).astype(np.uint8)
            g = np.clip((0.5 + SH_C0 * row['f_dc_1']) * 255, 0, 255).astype(np.uint8)
            b = np.clip((0.5 + SH_C0 * row['f_dc_2']) * 255, 0, 255).astype(np.uint8)
            a = np.clip((1 / (1 + np.exp(-row['opacity']))) * 255, 0, 255).astype(np.uint8)
            f.write(r.tobytes()); f.write(g.tobytes()); f.write(b.tobytes()); f.write(a.tobytes())
            
            # 4. Rotation (XYZW) - 4 bytes
            # Mapping based on standardize_ply logic: rot_1, 2, 3 are XYZ, rot_0 is W
            q = np.array([row['rot_1'], row['rot_2'], row['rot_3'], row['rot_0']], dtype=np.float32)
            mag = np.linalg.norm(q)
            if mag > 0: q /= mag
            rot_bytes = (q * 128 + 128).clip(0, 255).astype(np.uint8)
            f.write(rot_bytes.tobytes())

def standardize_ply(input_path, output_path):
    plydata = PlyData.read(input_path)
    if 'vertex' not in plydata: raise ValueError("No vertex element")
    
    data = plydata['vertex'].data
    num_points = len(data)
    
    # Filter NaNs
    required = ['x', 'y', 'z', 'f_dc_0', 'f_dc_1', 'f_dc_2', 'opacity', 
                'scale_0', 'scale_1', 'scale_2', 'rot_0', 'rot_1', 'rot_2', 'rot_3']
    valid_mask = np.ones(num_points, dtype=bool)
    for prop in required: valid_mask &= np.isfinite(data[prop])
    filtered_data = data[valid_mask]

    # Save Standard PLY
    dtype_standard = [('x', '<f4'), ('y', '<f4'), ('z', '<f4'),
                      ('scale_0', '<f4'), ('scale_1', '<f4'), ('scale_2', '<f4'),
                      ('rot_0', '<f4'), ('rot_1', '<f4'), ('rot_2', '<f4'), ('rot_3', '<f4'),
                      ('f_dc_0', '<f4'), ('f_dc_1', '<f4'), ('f_dc_2', '<f4'), ('opacity', '<f4')]
    new_data = np.empty(len(filtered_data), dtype=dtype_standard)
    for p in ['x', 'y', 'z', 'scale_0', 'scale_1', 'scale_2', 'f_dc_0', 'f_dc_1', 'f_dc_2', 'opacity']:
        new_data[p] = filtered_data[p]
    
    # ML-Sharp WXYZ to Standard XYZW
    new_data['rot_0'] = filtered_data['rot_1'] # x
    new_data['rot_1'] = filtered_data['rot_2'] # y
    new_data['rot_2'] = filtered_data['rot_3'] # z
    new_data['rot_3'] = filtered_data['rot_0'] # w

    vertex_element = PlyElement.describe(new_data, 'vertex')
    PlyData([vertex_element], text=False).write(output_path)
    
    # Save clean .splat version
    save_as_splat(new_data, output_path.replace('.ply', '.splat'))
    
    return len(new_data), num_points - len(new_data)
'''

    # Create a temporary file for the standardized output
    temp_output = ply_path.with_suffix('.ply.tmp')

    cmd = [
        str(MLSHARP_PYTHON),
        "-c", python_code,
        str(ply_path),
        str(temp_output)
    ]

    if verbose:
        cmd.append("-v")
        print(f"Standardizing PLY format: {ply_path.name}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )

        if verbose and result.stdout:
            print(result.stdout.strip())

        # Replace original file with standardized version
        if temp_output.exists():
            import shutil
            shutil.move(str(temp_output), str(ply_path))
            return True
        else:
            raise RuntimeError("Standardized PLY file was not created")

    except subprocess.CalledProcessError as e:
        # Clean up temp file if it exists
        if temp_output.exists():
            temp_output.unlink()

        error_msg = f"PLY standardization failed with exit code {e.returncode}\n"
        if e.stdout:
            error_msg += f"Output: {e.stdout}\n"
        if e.stderr:
            error_msg += f"Error: {e.stderr}"
        raise RuntimeError(error_msg)

    except Exception as e:
        # Clean up temp file if it exists
        if temp_output.exists():
            temp_output.unlink()
        raise RuntimeError(f"Unexpected error during PLY standardization: {e}")
