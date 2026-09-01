#!/bin/bash

if ! [[ "18.04 20.04 22.04 24.04" == *"$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2)"* ]];
then
    echo "Ubuntu $(grep VERSION_ID /etc/os-release | cut -d '"' -f 2) is not currently supported.";
    exit 1;
fi

# Set non-interactive mode to avoid prompts in CI. `sudo` resets the
# environment, so this also has to be passed explicitly on each `sudo` line
# below -- exporting it here only covers the unprivileged commands.
export DEBIAN_FRONTEND=noninteractive

UBUNTU_VERSION=$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2)
PACKAGE_FILE="packages-microsoft-prod.deb"
# Installed by the package below, on every Ubuntu version supported here.
MS_SOURCE_LIST="/etc/apt/sources.list.d/microsoft-prod.list"

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

# Every apt call below is wrapped in `timeout`. apt applies no overall cap to a
# mirror that accepts a connection and then stops sending data, so a stalled
# fetch produces no output and never exits -- the `|| true` guards cannot
# rescue a hang, only a non-zero exit. Bounding each call turns a bad mirror
# into a fast, retryable failure instead of a job that runs to its timeout.

# Refresh only the Microsoft repository index, using the source list the
# package above just installed. A full refresh also polls the Ubuntu archives,
# whose mirror pool is intermittently unreachable from CI runners, and that is
# the fetch that stalls. List-Cleanup is disabled so the indexes already baked
# into the runner image survive -- the driver's dependencies resolve from them.
sudo DEBIAN_FRONTEND=noninteractive timeout 120 apt-get update \
    -o Dir::Etc::sourcelist="$MS_SOURCE_LIST" \
    -o Dir::Etc::sourceparts="-" \
    -o APT::Get::List-Cleanup="0" \
    -o Acquire::Retries="3" \
    || echo "Warning: Failed to refresh the Microsoft package index."

# Install a package, continuing even if it fails due to network issues. If the
# first attempt fails, the runner's baked-in Ubuntu indexes are likely stale
# enough that a dependency no longer resolves, so retry once behind a full
# refresh -- still bounded, so a bad mirror costs minutes rather than hours.
install_package() {
    local package="$1"

    if sudo DEBIAN_FRONTEND=noninteractive ACCEPT_EULA=Y timeout 300 apt-get install -y "$package"; then
        return 0
    fi

    echo "Warning: Failed to install ${package}; refreshing all package indexes and retrying."
    sudo DEBIAN_FRONTEND=noninteractive timeout 300 apt-get update -o Acquire::Retries="3" || true
    sudo DEBIAN_FRONTEND=noninteractive ACCEPT_EULA=Y timeout 300 apt-get install -y "$package" \
        || echo "Warning: Failed to install ${package}"
}

install_package msodbcsql18
install_package mssql-tools18
