import sys
from cx_Freeze import setup, Executable

DEBUG = False

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
build_exe_options = {"includes": ["pyperclip", "tkinter"], "excludes": [], "include_files": []}

# base="Win32GUI" should be used only for Windows GUI app
if DEBUG:
    base = None
else:
    if sys.platform == "win32":
        base = "Win32GUI"

setup(
    name="Exception Proposal",
    version="0.1.0.0",
    options={"build_exe": build_exe_options},
    executables=[Executable("exception_proposal.py", base=base)]
)
