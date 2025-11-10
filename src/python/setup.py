from setuptools import setup, Extension
import pybind11

# Define compiler arguments for MSVC (Windows)
# Advanced optimization flags for maximum performance
extra_compile_args = [
    '/EHsc',        # Exception handling
    '/bigobj',      # Large object files
    '/std:c++17',   # C++17 standard
    '/O2',          # Optimization level 2
    '/Ob3',         # Aggressive inlining (new)
    '/Oi',          # Enable intrinsic functions (new)
    '/Ot',          # Favor fast code over small code (new)
    '/arch:AVX2',   # AVX2 instructions
    '/fp:fast',     # Fast floating-point (relaxed IEEE compliance) (new)
    '/GL',          # Whole program optimization (new)
    '/DNOMINMAX'    # Disable min/max macros
]

# Link-time optimization flags
extra_link_args = [
    '/LTCG',        # Link-time code generation (new)
]

ext_modules = [
    Extension(
        'dase_engine',
        ['../cpp/analog_universal_node_engine_avx2.cpp', '../cpp/python_bindings.cpp'],
        include_dirs=[
            pybind11.get_include(),
            '../cpp',  # Include cpp directory for header files
            '../../'   # Include project root for fftw3.h
        ],
        language='c++',
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        library_dirs=['../../'],  # FFTW library location
        libraries=['libfftw3-3']
    ),
]

setup(
    name='dase_engine',
    version='1.0',
    description='D-ASE Analog Engine C++ extension compiled with pybind11',
    ext_modules=ext_modules,
)