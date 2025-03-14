"""Helpers to check build environment before actual build of POT"""

import os
import sys
import glob
import tempfile
import subprocess

from setuptools.command.build_ext import customize_compiler, new_compiler


def _get_compiler():
    ccompiler = new_compiler()
    customize_compiler(ccompiler)
    return ccompiler


def compile_test_program(code, extra_preargs=[], extra_postargs=[]):
    """Check that some C code can be compiled and run"""
    ccompiler = _get_compiler()

    # extra_(pre/post)args can be a callable to make it possible to get its
    # value from the compiler
    if callable(extra_preargs):
        extra_preargs = extra_preargs(ccompiler)
    if callable(extra_postargs):
        extra_postargs = extra_postargs(ccompiler)

    start_dir = os.path.abspath(".")

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            os.chdir(tmp_dir)

            # Write test program
            with open("test_program.c", "w") as f:
                f.write(code)

            os.mkdir("objects")

            # Compile, test program
            ccompiler.compile(
                ["test_program.c"], output_dir="objects", extra_postargs=extra_postargs
            )

            # Link test program
            objects = glob.glob(os.path.join("objects", "*" + ccompiler.obj_extension))
            ccompiler.link_executable(
                objects,
                "test_program",
                extra_preargs=extra_preargs,
                extra_postargs=extra_postargs,
            )

            if "PYTHON_CROSSENV" not in os.environ:
                # Run test program if not cross compiling
                # will raise a CalledProcessError if return code was non-zero
                output = subprocess.check_output("./test_program")
                output = output.decode(sys.stdout.encoding or "utf-8").splitlines()
            else:
                # Return an empty output if we are cross compiling
                # as we cannot run the test_program
                output = []
        except Exception:
            raise
        finally:
            os.chdir(start_dir)

    return output, extra_postargs
