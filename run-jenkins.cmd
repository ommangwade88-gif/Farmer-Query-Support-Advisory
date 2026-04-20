@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "JENKINS_HOME=%cd%\jenkins-data"
set "WAR=%cd%\jenkins.war"
if not exist "%JENKINS_HOME%" mkdir "%JENKINS_HOME%"

echo.
if exist "%WAR%" (
  for %%I in ("%WAR%") do if %%~zI LSS 10000000 del /f /q "%WAR%" 2>nul
)
if not exist "%WAR%" (
  echo Downloading Jenkins LTS war ~90 MB, please wait...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%cd%'; $w = Join-Path (Get-Location) 'jenkins.war'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://get.jenkins.io/war-stable/latest/jenkins.war' -OutFile $w -UseBasicParsing"
  if errorlevel 1 (
    echo Download failed. Check internet and try again.
    pause
    exit /b 1
  )
)

set "JAVA=C:\Program Files\Common Files\Oracle\Java\javapath\java.exe"
if not exist "%JAVA%" set "JAVA=java"

cls
echo ========================================
echo  Jenkins running - DO NOT CLOSE THIS WINDOW
echo  Browser: http://127.0.0.1:8081
echo  Unlock: %JENKINS_HOME%\secrets\initialAdminPassword
echo.
echo  Run your Jenkinsfile: New Item - Pipeline - from SCM - Git
echo  Repo URL + branch main + Script Path: Jenkinsfile
echo ========================================
echo.

"%JAVA%" -jar "%WAR%" --httpPort=8081 --httpListenAddress=0.0.0.0
echo.
echo Jenkins stopped.
pause
