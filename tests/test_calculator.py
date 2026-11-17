import os

import numpy as np
import pytest
from ase import Atoms
from ase import units as U
from ase.build import molecule
from ase.calculators import calculator as ase_calc
from ase.optimize import BFGS

from pygfnff import GFNFF, SOLVENTS, gfnff


def _caffeine_atoms(caffeine, **kwargs) -> Atoms:
    Z, R = caffeine
    return Atoms(numbers=Z, positions=R * U.Bohr, calculator=GFNFF(**kwargs))


@pytest.mark.parametrize("solvent", ["", "water"])
def test_gradient_by_finite_difference(caffeine, solvent: str) -> None:
    Z, R = caffeine
    _, g = gfnff(Z, R, solvent=solvent)
    h = 1.0e-4
    for i, k in [(0, 0), (7, 1), (15, 2)]:
        dR = np.zeros_like(R)
        dR[i, k] = h
        ep = gfnff(Z, R + dR, solvent=solvent)[0]
        em = gfnff(Z, R - dR, solvent=solvent)[0]
        assert g[i, k] == pytest.approx((ep - em) / (2 * h), abs=1.0e-6)


def test_units_of_calculator(caffeine) -> None:
    Z, R = caffeine
    e, g = gfnff(Z, R)
    atoms = _caffeine_atoms(caffeine)
    assert atoms.get_potential_energy() == pytest.approx(e * U.Hartree)
    np.testing.assert_allclose(
        atoms.get_forces(), -g * U.Hartree / U.Bohr, atol=1.0e-10
    )


def test_solvent(caffeine) -> None:
    Z, R = caffeine
    e_gas = gfnff(Z, R)[0]
    e_water = gfnff(Z, R, solvent="water")[0]
    assert e_water < e_gas
    assert gfnff(Z, R, solvent="H2O")[0] == pytest.approx(e_water)
    assert gfnff(Z, R, solvent="none")[0] == pytest.approx(e_gas)
    assert gfnff(Z, R, solvent=None)[0] == pytest.approx(e_gas)
    assert "water" in SOLVENTS

    atoms = _caffeine_atoms(caffeine, solvent="water")
    assert atoms.get_potential_energy() == pytest.approx(e_water * U.Hartree)
    # changing the parameter afterwards must take effect
    atoms.calc.set(solvent="")
    assert atoms.get_potential_energy() == pytest.approx(e_gas * U.Hartree)


def test_charge(caffeine) -> None:
    Z, R = caffeine
    e0 = gfnff(Z, R)[0]
    e1 = gfnff(Z, R, charge=1)[0]
    assert e1 != pytest.approx(e0, abs=1.0e-6)

    atoms = _caffeine_atoms(caffeine, charge=1)
    assert atoms.get_potential_energy() == pytest.approx(e1 * U.Hartree)

    # the default is the (rounded) sum of the initial charges
    atoms = _caffeine_atoms(caffeine)
    charges = np.zeros(len(atoms))
    charges[:3] = 0.3333
    atoms.set_initial_charges(charges)
    assert atoms.get_potential_energy() == pytest.approx(e1 * U.Hartree)


def test_invalid_input(caffeine) -> None:
    Z, R = caffeine
    with pytest.raises(ValueError, match="solvent"):
        gfnff(Z, R, solvent="not-a-solvent")
    with pytest.raises(ValueError, match="shape"):
        gfnff(Z, R[:-1])
    with pytest.raises(ValueError, match="elements"):
        gfnff([1, 100], [[0, 0, 0], [0, 0, 2]])
    with pytest.raises(ValueError, match="elements"):
        gfnff([1, 0], [[0, 0, 0], [0, 0, 2]])
    with pytest.raises(ValueError, match="finite"):
        gfnff([1, 1], [[0, 0, 0], [0, 0, np.nan]])
    with pytest.raises(ValueError, match="charge"):
        gfnff(Z, R, charge=0.5)  # type: ignore

    atoms = _caffeine_atoms(caffeine, solvent="not-a-solvent")
    with pytest.raises(ase_calc.CalculatorSetupError):
        atoms.get_potential_energy()


def test_backend_failure_is_an_exception() -> None:
    """The Fortran backend must not terminate the Python process."""
    Z, R = [8, 1, 1], np.zeros((3, 3))  # all atoms at the same position
    with pytest.raises(RuntimeError):
        gfnff(Z, R)
    atoms = Atoms(numbers=Z, positions=R, calculator=GFNFF())
    with pytest.raises(ase_calc.CalculationFailed):
        atoms.get_potential_energy()
    # and the backend is still usable afterwards
    assert np.isfinite(gfnff([1, 1], [[0, 0, 0], [0, 0, 1.4]])[0])


def test_pbc(caffeine) -> None:
    atoms = _caffeine_atoms(caffeine)
    e = atoms.get_potential_energy()

    # a cell without PBC is just a box around the molecule
    atoms.set_cell([30.0, 30.0, 30.0])
    assert atoms.get_potential_energy() == pytest.approx(e)

    atoms.set_pbc(True)
    with pytest.raises(ase_calc.CalculatorSetupError):
        atoms.get_potential_energy()


def test_no_file_in_cwd(caffeine, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Z, R = caffeine
    gfnff(Z, R)
    _caffeine_atoms(caffeine).get_potential_energy()
    _caffeine_atoms(caffeine, cache_topology=True).get_potential_energy()
    assert os.listdir(tmp_path) == []
    assert os.getcwd() == os.path.realpath(tmp_path)


def test_cache_topology(caffeine) -> None:
    ref = _caffeine_atoms(caffeine)
    atoms = _caffeine_atoms(caffeine, cache_topology=True)
    assert atoms.get_potential_energy() == pytest.approx(
        ref.get_potential_energy(), abs=1.0e-10
    )
    np.testing.assert_allclose(
        atoms.get_forces(), ref.get_forces(), atol=1.0e-10
    )

    # After a displacement the cached topology (bonds, reference charges,
    # ...) still belongs to the first geometry, so the energy differs
    # slightly from the one with a regenerated topology ...
    rng = np.random.default_rng(0)
    dR = rng.normal(scale=0.01, size=atoms.positions.shape)
    for a in (ref, atoms):
        a.positions += dR
    e, f = atoms.get_potential_energy(), atoms.get_forces()
    assert e == pytest.approx(ref.get_potential_energy(), abs=1.0e-4)
    np.testing.assert_allclose(f, ref.get_forces(), atol=1.0e-3)
    # ... but it is a consistent potential energy surface
    h = 1.0e-4
    for i, k in [(0, 0), (7, 1), (15, 2)]:
        e_pm = []
        for sign in (+1, -1):
            a = atoms.copy()
            a.positions[i, k] += sign * h
            e_pm.append(atoms.calc.get_potential_energy(a))
        assert f[i, k] == pytest.approx(
            -(e_pm[0] - e_pm[1]) / (2 * h), abs=1e-5
        )
    assert atoms.get_potential_energy() == pytest.approx(e, abs=1.0e-10)

    # regenerate the topology on demand, on parameters & on composition
    atoms.calc.reset_topology()
    assert atoms.get_potential_energy() == pytest.approx(
        ref.get_potential_energy(), abs=1.0e-10
    )
    for calc in (ref.calc, atoms.calc):
        calc.set(solvent="water")
    assert atoms.get_potential_energy() == pytest.approx(
        ref.get_potential_energy(), abs=1.0e-10
    )
    water = molecule("H2O")
    assert atoms.calc.get_potential_energy(water) == pytest.approx(
        ref.calc.get_potential_energy(water), abs=1.0e-10
    )


def test_cache_topology_with_several_calculators(caffeine) -> None:
    """The backend has only one cache slot shared by all calculators."""
    co = Atoms(molecule("CO"), calculator=GFNFF(cache_topology=True))
    caf = _caffeine_atoms(caffeine, cache_topology=True)
    e_co, e_caf = co.get_potential_energy(), caf.get_potential_energy()
    for _ in range(3):
        co.calc.reset()
        caf.calc.reset()
        assert co.get_potential_energy() == pytest.approx(e_co, abs=1.0e-10)
        assert caf.get_potential_energy() == pytest.approx(e_caf, abs=1.0e-10)


def test_optimization_with_cache_topology() -> None:
    results = []
    for cache in (False, True):
        atoms = Atoms(
            molecule("CH3CH2OH"), calculator=GFNFF(cache_topology=cache)
        )
        BFGS(atoms, logfile=None).run(fmax=0.01, steps=200)
        assert np.abs(atoms.get_forces()).max() < 0.01
        results.append(atoms.get_potential_energy())
    assert results[0] == pytest.approx(results[1], abs=1.0e-3)
