# PyGFNFF

[![Pypi version](https://img.shields.io/pypi/v/pygfnff)](https://pypi.org/project/pygfnff/)
[![PyPI Downloads](https://static.pepy.tech/badge/pygfnff)](https://pepy.tech/projects/pygfnff)

PyGFNFF is a Python library that provides the [GFN-FF](https://github.com/pprcht/gfnff) (Generic Force Field) method for computational chemistry calculations. It is based on F2PY (Fortran to Python interface) and integrates with the Atomic Simulation Environment (ASE).

---

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
│   ├── conftest.py
│   ├── test_calculator.py
│   ├── test_caffeine.py
│   └── test_co_by_ase.py
├── CMakeLists.txt        # Root CMake configuration
└── pyproject.toml        # Python project configuration
```

## Key Components

### Python Interface (`pygfnff/`)

- **`GFNFF`**: ASE Calculator subclass for non-PBC systems (units: Å & eV)
- **`gfnff()`**: Low-level function for single-point energy calculations (units: Bohr & Hartree)
- **`SOLVENTS`**: Names of the solvents available for the ALPB solvent model

### Fortran Backend (`fortran/`)

- GFN-FF implementation derived from https://github.com/pprcht/gfnff (commit 0491df2)
- GBSA solvation model support (optional, enabled via CMake `WITH_GBSA`)
- F2PY bindings via `_pygfnfflib.f90`
- The Fortran source code of GFN-FF is licensed under LGPL-3.0 by its authors, this package is distributed under GPL-3.0 (see `LICENSE`)


## Usage

There is an `ase.Calculator` subclass termed `GFNFF` for non-PBC system. And a more low function called `gfnff` can be found in [the code](https://github.com/LiuGaoyong/PyGFNFF/blob/main/pygfnff/_pygfnff.py).

```python
from ase import Atoms
from ase.build import molecule
from ase.optimize import BFGS
from scipy.spatial.distance import pdist

from pygfnff import GFNFF

atoms = Atoms(molecule("CO"), calculator=GFNFF())
opt = BFGS(atoms, logfile="-", trajectory=None)
opt.run(fmax=0.03, steps=50)
e = atoms.get_potential_energy()
print(f"Energy: {atoms.get_potential_energy():.3f}eV")
print(f"C=O Length: {pdist(atoms.positions).item():.3f}\u212b")

# Output:
#       Step     Time          Energy          fmax
# BFGS:    0 19:56:53       -9.188347        2.478131
# BFGS:    1 19:56:53       -9.050233        7.166941
# BFGS:    2 19:56:53       -9.215231        0.433918
# BFGS:    3 19:56:53       -9.215990        0.070653
# BFGS:    4 19:56:53       -9.216011        0.000889
# Energy: -9.216eV
# C=O Length: 1.129Å
```

### Options of the `GFNFF` calculator

```python
from pygfnff import GFNFF, SOLVENTS

print(sorted(SOLVENTS))  # ['acetone', 'acetonitrile', ..., 'water', 'woctanol']
calc = GFNFF(
    solvent="water",      # ALPB solvent model, defaults to "" (gas phase)
    charge=None,          # total charge, defaults to the rounded sum of `atoms.get_initial_charges()`
    cache_topology=True,  # defaults to False
)
```

- **`cache_topology=False`** (default): the GFN-FF topology (bonds, reference charges, ...) is regenerated from the current positions in every calculation.
- **`cache_topology=True`**: the topology is generated only once, from the positions of the first calculation, and reused as long as the atomic numbers, the charge and the solvent are unchanged. This is how GFN-FF is used in `xtb`: it is faster and gives a smooth potential energy surface for optimization & MD, but bonds can never break or form. Use `calc.reset_topology()` to regenerate the topology from the next positions.

The low-level function works in atomic units:

```python
from pygfnff import gfnff

# numbers: (N,), positions: (N, 3) in Bohr
energy, gradient = gfnff(numbers, positions, solvent="water", charge=0)
# energy in Hartree, gradient in Hartree/Bohr
```

Invalid input raises `ValueError`, a failure in the Fortran backend raises `RuntimeError` (`ase.calculators.calculator.CalculatorSetupError` & `CalculationFailed` for the calculator).

### Limitations

- Periodic boundary conditions are not supported.
- Only the elements with Z = 1-86 are supported.
- The Fortran backend keeps global state, so the calculations are serialized by a lock: threads do not run in parallel (use processes instead).

### Reference

1. S.Spicher, S.Grimme. Robust Atomistic Modeling of Materials, Organometallic, and Biochemical Systems (2020), DOI: https://doi.org/10.1002/anie.202004239
2. A standalone library of the GFN-FF method. https://github.com/pprcht/gfnff/
