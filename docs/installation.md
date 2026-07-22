# Installation Guide

## Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- Linux operating system

## Supported Distributions

- Ubuntu 20.04+
- Debian 11+
- Kali Linux
- Fedora 36+
- RHEL 8+
- Rocky Linux 8+
- AlmaLinux 8+
- Arch Linux
- openSUSE Leap/Tumbleweed

## Install from Source

```bash
# Clone the repository
git clone https://github.com/shellsense-ai/shellsense.git
cd shellsense-ai

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .

# Verify installation
ss --version
ss doctor
```

## Install via Installer Script

```bash
git clone https://github.com/shellsense-ai/shellsense.git
cd shellsense-ai
bash installer/install.sh
```

## Verifying Installation

Run the doctor command to verify everything is set up correctly:

```bash
ss doctor
```

This checks:

- Operating system compatibility
- Python version
- Required packages
- Configuration files
- Database initialization

## Next Steps

- Run `ss info` to view system information
- Run `ss config show` to view default configuration
- Read the [Developer Guide](developer-guide.md) for development setup
