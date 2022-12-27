from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
build_exe_options = {"includes": ["tkinter"], "include_files": ["icon.ico"]}

# base = "Win32GUI" should be used only for Windows GUI app

base = None

setup(
    name="easy_service",
    version="0.1.0.2",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, icon="icon.ico")]
)
