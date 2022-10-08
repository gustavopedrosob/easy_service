from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
build_exe_options = {"includes": ["pyperclip", "tkinter"]}

# base="Win32GUI" should be used only for Windows GUI app

base = "Win32GUI"

setup(
    name="Exception Proposal",
    version="0.1.0.0",
    options={"build_exe": build_exe_options},
    executables=[Executable("exception_proposal_app.py", base=base)]
)
