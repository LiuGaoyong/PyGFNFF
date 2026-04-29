# PyGFNFF

## Project Overview

PyGFNFF is a Python library that provides the GFN-FF (Generic Force Field) method for computational chemistry calculations. It is based on F2PY (Fortran to Python interface) and integrates with the Atomic Simulation Environment (ASE).

**Reference:**
- S.Spicher, S.Grimme. Robust Atomistic Modeling of Materials, Organometallic, and Biochemical Systems (2020), DOI: https://doi.org/10.1002/anie.202004239
- Original Fortran implementation: https://github.com/pprcht/gfnff/

## Project Structure

```
PyGFNFF/
├── pygfnff/              # Python package
│   ├── __init__.py       # Exports GFNFF calculator and gfnff function
│   └── _pygfnff.py       # Main implementation
├── fortran/              # Fortran source code
│   ├── gfnff_*.f90       # GFN-FF modules
│   ├── _pygfnfflib.f90   # F2PY interface
│   ├── CMakeLists.txt    # Fortran build configuration
│   └── gbsa/             # GBSA solvation model
├── include/              # C header and parameter files
│   ├── gfnff_interface_c.h
│   └── param_*.fh        # Parameter files for solvents
├── tests/                # Test suite
│   ├── test_co_by_ase.py
│   └── test_coffeine.py
├── CMakeLists.txt        # Root CMake configuration
└── pyproject.toml        # Python project configuration
```

## Key Components

### Python Interface (`pygfnff/`)

- **`GFNFF`**: ASE Calculator subclass for non-PBC systems
- **`gfnff()`**: Low-level function for single-point energy calculations

### Fortran Backend (`fortran/`)

- GFN-FF implementation derived from https://github.com/pprcht/gfnff (commit 0491df2)
- GBSA solvation model support (optional, enabled via CMake `WITH_GBSA`)
- F2PY bindings via `_pygfnfflib.f90`

## Build System

- **Build backend**: scikit-build-core
- **Fortran build**: CMake with Ninja generator
- **Required compilers**: GNU Fortran or Intel Fortran
- **Dependencies**: LAPACK, OpenBLAS, OpenMP (optional)

## Development Commands

```bash
# Install dependencies
uv sync

# Run tests
pytest tests/

# Build wheel (requires fortran compiler)
pipx run --python 3.13 cibuildwheel==3.1.1
```

## Usage Example

```python
from ase import Atoms
from ase.build import molecule
from ase.optimize import BFGS
from pygfnff import GFNFF

atoms = Atoms(molecule("CO"), calculator=GFNFF())
opt = BFGS(atoms, logfile="-", trajectory=None)
opt.run(fmax=0.03, steps=50)
e = atoms.get_potential_energy()
```

## Configuration

- `pyproject.toml`: Project metadata, dependencies, build settings
- `.python-version`: Python version specification
- `.github/workflows/`: CI/CD pipelines for pytest and wheel building
