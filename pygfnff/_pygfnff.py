import threading
from typing import Any, Optional

import numpy as np
import numpy.typing as npt
from ase import Atoms
from ase import units as U
from ase.calculators import calculator as ase_calc
from typing_extensions import override

#: Solvents parametrised for the GFN-FF/ALPB model (lower case).
SOLVENTS: frozenset[str] = frozenset(
    {
        "acetone",
        "acetonitrile",
        "aniline",
        "benzaldehyde",
        "benzene",
        "ch2cl2",
        "chcl3",
        "chloroform",
        "cs2",
        "dichlormethane",
        "dioxane",
        "dmf",
        "dmso",
        "ethanol",
        "ether",
        "ethylacetate",
        "furane",
        "h2o",
        "hexadecane",
        "hexane",
        "methanol",
        "n-hexan",
        "n-hexane",
        "nhexan",
        "nhexane",
        "nitromethane",
        "octanol",
        "phenol",
        "thf",
        "toluene",
        "water",
        "woctanol",
    }
)

#: The heaviest element supported by GFN-FF (Rn).
MAX_Z = 86

# The Fortran backend keeps module-level state and holds a single cached
# topology, so calls into it are serialised and the cache has one owner.
_LOCK = threading.RLock()
_cache_owner: Optional[object] = None


def _backend() -> Any:
    try:
        from . import _pygfnfflib  # type: ignore
    except ImportError as e:
        raise ImportError("The pygfnff fortran backend not available.") from e
    return _pygfnfflib.gfnff


def _prepare(
    numbers: npt.ArrayLike,
    positions: npt.ArrayLike,
    solvent: Optional[str],
    charge: int,
) -> tuple[np.ndarray, np.ndarray, str, int]:
    """Validate the input, the Fortran backend must never see bad input."""
    numbers = np.asarray(numbers, dtype=np.intc).flatten()
    positions = np.asarray(positions, dtype=np.float64)
    if len(numbers) == 0:
        raise ValueError("At least one atom is required.")
    if positions.shape != (len(numbers), 3):
        raise ValueError(
            f"The shape of positions must be ({len(numbers)}, 3), "
            f"but got {positions.shape}."
        )
    if not np.isfinite(positions).all():
        raise ValueError("The positions must be finite.")
    if numbers.min() < 1 or numbers.max() > MAX_Z:
        raise ValueError(
            f"GFN-FF only supports the elements with Z = 1-{MAX_Z}."
        )
    if int(charge) != charge:
        raise ValueError(f"The total charge must be an integer: {charge}.")
    solvent = "" if solvent is None else str(solvent).strip().lower()
    if solvent == "none":
        solvent = ""
    if solvent != "" and solvent not in SOLVENTS:
        raise ValueError(
            f"Unknown solvent: {solvent!r}. "
            f"Available solvents: {', '.join(sorted(SOLVENTS))}."
        )
    xyz = np.asfortranarray(positions.T, dtype=np.float64)
    return numbers, xyz, solvent, int(charge)


def _check(iostat: int) -> None:
    if iostat == 0:
        return
    elif iostat == 1:
        raise RuntimeError("Fail to generate GFNFF topology.")
    elif iostat == 2:
        raise RuntimeError("Fail to perform SPE calculation.")
    elif iostat == 3:
        raise RuntimeError("No cached GFNFF topology is available.")
    else:
        raise RuntimeError("Unknown error in Fortran backend.")


def gfnff(
    numbers: npt.ArrayLike,
    positions: npt.ArrayLike,
    solvent: Optional[str] = "",
    charge: int = 0,
) -> tuple[float, np.ndarray]:
    """Run single point energy calculation by GFNFF.

    The topology is generated from the given positions on every call.

    Args:
        numbers (np.ndarray): The atomic numbers.
        positions (np.ndarray): The atomic positions (unit: Bohr).
        solvent (str, optional): The solvent by ALPB solvent model,
            one of `pygfnff.SOLVENTS`. Defaults to empty string
            means turn off solvent model.
        charge (int, optional): The total charge. Defaults to 0.

    Returns:
        tuple[float, np.ndarray]:
            The first is the energy in Hartree.
            The second is the gradient in Hartree/Bohr.

    Raises:
        ValueError: If the input is invalid.
        RuntimeError: If the calculation fails in the Fortran backend.
    """
    lib = _backend()
    numbers, xyz, solvent, charge = _prepare(
        numbers, positions, solvent, charge
    )
    with _LOCK:
        iostat, energy, grad = lib.gfnff_sp(charge, numbers, xyz, solvent)
    _check(iostat)
    return float(energy), np.ascontiguousarray(grad.T)


class GFNFF(ase_calc.Calculator):
    """GFNFF calculator in ASE.

    Parameters:
        solvent (str): The solvent by ALPB solvent model, one of
            `pygfnff.SOLVENTS`. Defaults to empty string means gas phase.
        charge (int, optional): The total charge. Defaults to None means
            the rounded sum of the initial charges of the atoms.
        cache_topology (bool): Defaults to False, the topology is generated
            from the current positions in every calculation. If True, the
            topology is generated only once (from the positions of the
            first calculation) and reused as long as the atomic numbers,
            the charge and the solvent are unchanged, which is much faster
            for optimization & MD. Call `reset_topology` to regenerate it.
    """

    implemented_properties = [
        "energy",
        "forces",
    ]

    # `calc.set(solvent=...)` etc. must invalidate the previous results
    discard_results_on_any_change = True

    default_parameters = {
        "solvent": "",
        "charge": None,
        "cache_topology": False,
    }

    def __init__(self, *args, **kwargs) -> None:
        self._topo_key: Optional[tuple] = None
        self._topo_xyz: Optional[np.ndarray] = None
        super().__init__(*args, **kwargs)

    def reset_topology(self) -> None:
        """Drop the cached topology, the next calculation regenerates it."""
        self._topo_key = None
        self._topo_xyz = None
        self.results = {}

    def _get_charge(self, atoms: Atoms) -> int:
        charge = self.parameters["charge"]
        if charge is None:
            charge = round(float(atoms.get_initial_charges().sum()))
        return charge

    def _calculate_cached(
        self,
        numbers: np.ndarray,
        xyz: np.ndarray,
        solvent: str,
        charge: int,
    ) -> tuple[float, np.ndarray]:
        global _cache_owner
        lib = _backend()
        key = (numbers.tobytes(), solvent, charge)
        with _LOCK:
            if self._topo_key != key or self._topo_xyz is None:
                self._topo_key, self._topo_xyz = key, xyz.copy(order="F")
                _cache_owner = None
            if _cache_owner is not self:
                # (Re)generate the topology from the reference positions,
                # so the result is independent of other calculators.
                _cache_owner = None
                _check(lib.gfnff_init(charge, numbers, self._topo_xyz, solvent))
                _cache_owner = self
            iostat, energy, grad = lib.gfnff_energy(numbers, xyz)
            if iostat != 0:
                _cache_owner = None
        _check(iostat)
        return float(energy), np.ascontiguousarray(grad.T)

    @override
    def calculate(
        self,
        atoms: Optional[Atoms] = None,
        properties: Optional[list[str]] = None,
        system_changes: list[str] = ase_calc.all_changes,
    ) -> None:
        """Perform actual calculation by GFNFF."""
        super().calculate(atoms, properties, system_changes)
        assert isinstance(self.atoms, Atoms)
        if self.atoms.pbc.any():
            raise ase_calc.CalculatorSetupError(
                "PBC system is not supported yet by pygfnff backend."
            )

        try:
            numbers, xyz, solvent, charge = _prepare(
                self.atoms.numbers,
                self.atoms.positions * U.Angstrom / U.Bohr,
                solvent=self.parameters["solvent"],
                charge=self._get_charge(self.atoms),
            )
            if self.parameters["cache_topology"]:
                energy, gradient = self._calculate_cached(
                    numbers, xyz, solvent, charge
                )
            else:
                energy, gradient = gfnff(numbers, xyz.T, solvent, charge)
        except ImportError as e:
            raise ase_calc.CalculatorError(str(e)) from e
        except ValueError as e:
            raise ase_calc.CalculatorSetupError(str(e)) from e
        except RuntimeError as e:
            raise ase_calc.CalculationFailed(
                f"Error in Fortran backend: {e}"
            ) from e

        self.results.update(
            dict(
                energy=energy * U.Hartree / U.eV,
                forces=-gradient * (U.Hartree / U.Bohr) / (U.eV / U.Angstrom),
            )
        )
