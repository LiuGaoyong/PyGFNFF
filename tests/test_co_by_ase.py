import pytest
from ase import Atoms
from ase.build import molecule
from ase.optimize import BFGS
from scipy.spatial.distance import pdist

from pygfnff import GFNFF


def get_co() -> Atoms:
    atoms = Atoms(molecule("CO"), calculator=GFNFF())
    print(f"Energy: {atoms.get_potential_energy():.3f}eV")
    print("Forces: \n", atoms.get_forces())
    print("Positions: \n", atoms.positions)
    opt = BFGS(atoms, logfile="-", trajectory=None)
    opt.run(fmax=0.03, steps=50)
    return atoms


def test_co() -> None:
    atoms = get_co()
    e = atoms.get_potential_energy()
    bl = pdist(atoms.positions).item()
    print(f"Energy: {e:.3f}eV")
    print(f"C=O Length: {bl:.3f}\u212b")
    pytest.approx(1.3, bl, abs=0.02)
    pytest.approx(-9.216011, e, abs=1.0e-3)
