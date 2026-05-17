@echo off
echo Installing Spectrum Security...
winget install -e --id Python.Python.3.11 --silent --accept-package-agreements
call refreshenv
pip install spectrum-security
echo Spectrum installed. Run 'spectrum' to start.
