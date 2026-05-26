@echo off
echo Starting AI Banking backend...
pushd "%~dp0backend"
call .venv\Scripts\activate
start http://127.0.0.1:8000/docs
python -m uvicorn app.main:app --reload
popd
pause