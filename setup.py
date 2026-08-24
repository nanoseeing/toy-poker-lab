from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup


setup(
    ext_modules=[
        Pybind11Extension(
            "toy_poker._range_solver_cpp",
            ["src/toy_poker/solvers/cpp/range_solver.cpp"],
            cxx_std=20,
            extra_compile_args=["-O3", "-DNDEBUG"],
        )
    ],
    cmdclass={"build_ext": build_ext},
)
