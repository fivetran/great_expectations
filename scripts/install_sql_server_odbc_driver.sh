#!/bin/bash

if ! [[ "18.04 20.04 22.04 24.04" == *"$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2)"* ]];
then
    echo "Ubuntu $(grep VERSION_ID /etc/os-release | cut -d '"' -f 2) is not currently supported.";
    exit 1;
fi

# Set non-interactive mode to avoid prompts in CI
export DEBIAN_FRONTEND=noninteractive

UBUNTU_VERSION=$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2)
PACKAGE_FILE="packages-microsoft-prod.deb"

# Download the package to configure the Microsoft repo
if ! curl -sSL --connect-timeout 10 --max-time 30 -o "$PACKAGE_FILE" "https://packages.microsoft.com/config/ubuntu/${UBUNTU_VERSION}/packages-microsoft-prod.deb"; then
    echo "Warning: Failed to download Microsoft packages repository configuration. packages.microsoft.com may be down."
    exit 1
fi

# Verify the file was downloaded
if [ ! -f "$PACKAGE_FILE" ] || [ ! -s "$PACKAGE_FILE" ]; then
    echo "Warning: Downloaded file is missing or empty."
    exit 1
fi

sudo dpkg --force-confdef --force-confold -i "$PACKAGE_FILE" || true
# Delete the file
rm -f "$PACKAGE_FILE"

sudo apt-get update || true

# Install packages, continuing even if they fail due to network issues
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 || echo "Warning: Failed to install msodbcsql18"
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18 || echo "Warning: Failed to install mssql-tools18"
