try:
    from pygfnff import _pygfnfflib  # type: ignore

    print(help(_pygfnfflib))
except ImportError:
    from pygfnff._pygfnfflib import gfnff_sp  # type: ignore

    print(help(gfnff_sp))
