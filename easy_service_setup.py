from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
build_exe_options = {"includes": ["tkinter"]}

# base="Win32GUI" should be used only for Windows GUI app

base = "Win32GUI"

setup(
    name="easy_service",
    version="0.1.0.0",
    options={"build_exe": build_exe_options},
    executables=[Executable("easy_service.py", base=base)]
)
