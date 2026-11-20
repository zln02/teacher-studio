@echo off
rem Run a Teacher Studio script with whatever Python exists: the path doctor.py recorded, else py / python / python3.
rem Usage: scripts\run.cmd studio.py doctor   (script names are relative to this folder)
setlocal
set "PYTHONUTF8=1"
set "TS_PY="
set "TS_ENV=%TEACHER_STUDIO_HOME%"
if "%TS_ENV%"=="" set "TS_ENV=%USERPROFILE%\.teacher-studio"
if exist "%TS_ENV%\env.json" (
  for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "try{(Get-Content -Raw -Encoding UTF8 '%TS_ENV%\env.json' | ConvertFrom-Json).python_path}catch{}"`) do set "TS_PY=%%P"
)
if defined TS_PY if not exist "%TS_PY%" set "TS_PY="
if not defined TS_PY (
  for %%C in (py python python3) do (
    if not defined TS_PY (
      %%C -c "import sys" >nul 2>nul && set "TS_PY=%%C"
    )
  )
)
if not defined TS_PY (
  echo Python을 찾지 못했어요. py, python, python3 중 하나가 필요해요. 1>&2
  exit /b 127
)
set "TS_SCRIPT=%~1"
shift
if not "%TS_SCRIPT:~1,1%"==":" if not "%TS_SCRIPT:~0,1%"=="\" set "TS_SCRIPT=%~dp0%TS_SCRIPT%"
set "TS_ARGS="
:loop
if "%~1"=="" goto go
set TS_ARGS=%TS_ARGS% "%~1"
shift
goto loop
:go
"%TS_PY%" "%TS_SCRIPT%" %TS_ARGS%
exit /b %errorlevel%
