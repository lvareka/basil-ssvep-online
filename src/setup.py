import sys
from cx_Freeze import setup, Executable

build_exe_options =  {"packages": ["data", "gui", "processing"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "lsl_ssvep",
        version = "1.0",
        description = "BASIL SSVEP BCI",
        options =  {"build_exe": build_exe_options},
        executables = [Executable("src/cmd.py", base=base)])