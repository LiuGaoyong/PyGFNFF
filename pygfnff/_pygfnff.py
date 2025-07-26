from pathlib import Path

import numpy as np
import numpy.typing as npt


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
            The second is the forces in Hartree/Bohr.
    """
    try:
        import pygfnff._pygfnfflib as lib  # type: ignore
    except ImportError:
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
