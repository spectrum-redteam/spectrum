import PyInstaller.__main__
import platform
import sys

# Determine target filename
system = platform.system().lower()
machine = platform.machine().lower()

if system == "darwin":
    if machine == "arm64":
        name = "spectrum-darwin-arm64"
    else:
        name = "spectrum-darwin-amd64"
elif system == "linux":
    name = "spectrum-linux-amd64"
elif system == "windows":
    name = "spectrum-windows-amd64"
else:
    name = f"spectrum-{system}-{machine}"

PyInstaller.__main__.run([
    "--onefile",
    "--name", name,
    "--clean",
    "--noconfirm",
    "--distpath", "release",
    "--workpath", "build_temp",
    "--specpath", "build_temp",
    "--add-data", "spectrum/modules:spectrum/modules",
    "-m", "spectrum.main",
])

print(f"\nBinary created: release/{name}")
