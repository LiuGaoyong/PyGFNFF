import os
from pathlib import Path
from tempfile import mkdtemp
from typing import Optional

import numpy as np
import numpy.typing as npt
from ase import Atoms
from ase import units as U
from ase.calculators import calculator as ase_calc
from typing_extensions import override


def gfnff(
    numbers: npt.ArrayLike,
    positions: npt.ArrayLike,
    solvent: str = "",
    charge: int = 0,
) -> tuple[float, np.ndarray]:
    """Run single point energy calculation by GFNFF.

    Args:
        numbers (np.ndarray): The atomic numbers.
        positions (np.ndarray): The atomic postions (unit: Bohr).
        solvent (str, optional): The solvent by ALPB solvent model.
            Defaults to empty string means turn off solvent model.
        charge (int, optional): The total charge. Defaults to 0.

    Returns:
        tuple[float, np.ndarray]:
            The first is the energy in Hartree.
            The second is the gradient in Hartree/Bohr.
    """
    try:
        import pygfnff  # noqa: F401
        import pygfnff._pygfnfflib as lib  # type: ignore
    except ImportError:
        print(list[Path(__file__).parent.glob("*")])
        raise ImportError("The pygfnff fortran backend not available.")

    numbers = np.asarray(numbers, dtype=int).flatten()
    positions = np.asarray(positions, dtype=np.float64)
    assert positions.shape == (len(numbers), 3)
    charge = int(charge)

    if solvent == "":
        iostat, energy, grad = lib.gfnff.gfnff_sp(
            len(numbers),
            charge,
            numbers,
            np.asfortranarray(positions.T, dtype=np.float64),
        )
    else:
        raise NotImplementedError
    if iostat == 0:
        for postfix in ("topo", "adjacency"):
            f = Path().joinpath(f"gfnff_{postfix}")
            if f.exists() and f.is_file():
                f.unlink()
        return energy, grad.T
    elif iostat == 1:
        raise RuntimeError("Fail to generate GFNFF topology.")
    elif iostat == 2:
        raise RuntimeError("Fail to perform SPE calculation.")
    else:
        raise RuntimeError("Unknown error in Fortran backend.")


class GFNFF(ase_calc.Calculator):
    """GFNFF calculator in ASE."""

    implemented_properties = [
        "energy",
        "forces",
    ]

    default_parameters = {
        "solvent": "",
    }

    def __init__(
        self,
        restart=None,
        ignore_bad_restart_file=ase_calc.BaseCalculator._deprecated,
        label=None,
        atoms: Optional[Atoms] = None,
        directory: str = mkdtemp(),  # type: ignore
        **kwargs,
    ) -> None:
        super().__init__(
            atoms=atoms,
            label=label,
            restart=restart,
            ignore_bad_restart_file=ignore_bad_restart_file,
            directory=Path(directory).absolute().__fspath__(),
            **kwargs,
        )
        assert isinstance(self.parameters, ase_calc.Parameters)
        self.__solvent = str(self.parameters["solvent"])
        # TODO: check solvent support.

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
        if any(self.atoms.pbc) or self.atoms.cell.array.any():
            raise ase_calc.CalculatorSetupError(
                "PBC system is not supported yet by pygfnff backend."
            )

        try:
            cwd = Path().cwd()
            os.chdir(self.directory)
            energy, gradient = gfnff(
                self.atoms.numbers,
                self.atoms.positions * U.Angstrom / U.Bohr,
                solvent=self.__solvent,
                charge=int(self.atoms.get_initial_charges().sum()),
            )
            os.chdir(cwd)
        except ImportError as e:
            raise ase_calc.CalculatorError(e)
        except RuntimeError as e:
            raise ase_calc.CalculationFailed(f"Error in Fortran backend: {e}.")

        self.results.update(
            dict(
                energy=energy * U.Hartree / U.eV,
                forces=-gradient * (U.Hartree / U.Bohr) / (U.eV / U.Angstrom),
            )
        )
