@echo off
echo Building UniFi Camera Manager for Raspberry Pi...

REM Enable Docker experimental features for ARM emulation
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

REM Build the Docker image for ARM32v7
docker build -f Dockerfile.rpi -t unifi-camera-rpi .

REM Create output directory
if not exist "dist-rpi" mkdir dist-rpi

REM Run container and copy executable
docker run --rm -v %cd%\dist-rpi:/host-output unifi-camera-rpi

echo.
echo Build complete! Executable is in dist-rpi\unifi-camera-manager
echo Copy this file to your Raspberry Pi and run it.
pause 