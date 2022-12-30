from cx_Freeze import setup, Executable

from common import config

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
build_exe_options = {"includes": ["tkinter"], "include_files": ["icon.ico"]}

# base = "Win32GUI" should be used only for Windows GUI app

base = "Win32GUI"

setup(
    name="easy_service",
    version=f"0.{config.VERSION}",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, icon="icon.ico")]
)
