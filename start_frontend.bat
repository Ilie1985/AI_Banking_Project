@echo off
echo Starting AI Banking frontend...
pushd "%~dp0frontend"
start http://127.0.0.1:5500/index.html?v=14
python -m http.server 5500
popd
pause