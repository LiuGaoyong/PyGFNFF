try:
    import numpy as np
    from ase.atoms import Atoms

    from pygfnff import _pygfnfflib as lib  # type: ignore

    def gfnff(atoms: Atoms) -> tuple[float, np.ndarray]:
        """Run GFNFF calculation on a given ASE Atoms object."""
        if atoms.pbc.any():
            raise ValueError("Periodic boundary conditions are not supported.")

        nat: int = len(atoms)
        ichrg = int(atoms.get_initial_charges().sum())
        result = lib.gfnff.gfnff_sp(
            nat,
            ichrg,
            atoms.numbers.flatten(),
            atoms.positions.flatten(),
        )
        print(result)
        return result

except ImportError:
    raise ImportError("The pygfnff backend is not availible. ")


if __name__ == "__main__":
    from ase.build import molecule

    atoms = molecule("H2O")
    gfnff(atoms)
