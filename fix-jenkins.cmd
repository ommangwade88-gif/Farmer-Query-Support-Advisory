@echo off
echo ========================================
echo  FIXING JENKINS WITH DOCKER SUPPORT
echo ========================================
echo.

echo [1/6] Stopping Jenkins container...
docker stop Jenkin
echo.

echo [2/6] Removing old container (data is safe in volume)...
docker rm Jenkin
echo.

echo [3/6] Starting new Jenkins with Docker socket mounted...
docker run -d ^
  --name Jenkin ^
  -p 8082:8080 ^
  -p 50000:50000 ^
  -v dcc3e14ca2c1287725b1c3bfde987e9af6927d8159e0b3620cad035a91f431ee:/var/jenkins_home ^
  -v //var/run/docker.sock:/var/run/docker.sock ^
  -v "%cd%":/workspace ^
  jenkins/jenkins:lts

echo.
echo [4/6] Waiting for Jenkins to start (30 seconds)...
timeout /t 30 /nobreak >nul
echo.

echo [5/6] Installing Docker CLI inside Jenkins...
docker exec -u root Jenkin apt-get update -qq
docker exec -u root Jenkin apt-get install -y docker.io
docker exec -u root Jenkin usermod -aG docker jenkins
echo.

echo [6/6] Restarting Jenkins to apply changes...
docker restart Jenkin
echo.

echo ========================================
echo  DONE! Waiting 20 seconds for Jenkins...
echo ========================================
timeout /t 20 /nobreak >nul

echo.
echo Testing Docker inside Jenkins...
docker exec Jenkin docker ps
echo.

if %ERRORLEVEL% EQU 0 (
    echo SUCCESS! Docker is working inside Jenkins.
    echo.
    echo Open: http://localhost:8082
    echo Job already exists: "devops project1"
    echo.
    echo Next: Add Docker Hub credentials with ID: dockerhub-credentials
) else (
    echo WARNING: Docker test failed. Try manually:
    echo   docker exec Jenkin docker ps
)

pause
