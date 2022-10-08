from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
build_exe_options = {"includes": ["pyperclip", "tkinter"]}

# base="Win32GUI" should be used only for Windows GUI app

base = "Win32GUI"

setup(
    name="Refusal",
    version="0.1.0.0",
    options={"build_exe": build_exe_options},
    executables=[Executable("refusal_app.py", base=base)]
)
