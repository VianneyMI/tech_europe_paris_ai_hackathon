#!/bin/bash

# UV Complete Reset Script
# This script will completely remove uv and all its data, then reinstall it fresh

set -e  # Exit on any error

echo "ðŸ§¹ Starting UV complete reset..."
echo "=================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to safely remove directory
safe_remove() {
    if [ -d "$1" ]; then
        echo "ðŸ“ Removing: $1"
        rm -rf "$1"
    else
        echo "ðŸ“ Directory not found (skipping): $1"
    fi
}

# Function to safely remove file
safe_remove_file() {
    if [ -f "$1" ]; then
        echo "ðŸ“„ Removing: $1"
        rm -f "$1"
    else
        echo "ðŸ“„ File not found (skipping): $1"
    fi
}

echo ""
echo "Step 1: Killing any running uv processes..."
echo "--------------------------------------------"
if pgrep -f "uv" > /dev/null; then
    echo "ðŸ”ª Killing uv processes..."
    pkill -9 -f "uv" || echo "   No uv processes to kill"
else
    echo "âœ… No uv processes running"
fi

echo ""
echo "Step 2: Removing uv data directories..."
echo "---------------------------------------"
safe_remove "$HOME/.local/share/uv"
safe_remove "$HOME/.cache/uv"
safe_remove "$HOME/.config/uv"

echo ""
echo "Step 3: Removing uv binaries..."
echo "-------------------------------"
# Common installation locations
safe_remove_file "$HOME/.cargo/bin/uv"
safe_remove_file "$HOME/.local/bin/uv"
safe_remove_file "/usr/local/bin/uv"
safe_remove_file "/opt/homebrew/bin/uv"

# Check if uv was installed via Homebrew
if command_exists brew; then
    if brew list uv &>/dev/null; then
        echo "ðŸº Removing uv via Homebrew..."
        brew uninstall uv || echo "   Could not uninstall via Homebrew"
    fi
fi

echo ""
echo "Step 4: Cleaning project-specific files..."
echo "------------------------------------------"
if [ -d ".venv" ]; then
    echo "ðŸ—‚ï¸  Removing .venv directory..."
    rm -rf .venv
fi

if [ -f "uv.lock" ]; then
    echo "ðŸ”’ Removing uv.lock file..."
    rm -f uv.lock
fi

echo ""
echo "Step 5: Reinstalling uv..."
echo "--------------------------"
if command_exists curl; then
    echo "ðŸ“¥ Downloading and installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "âŒ curl not found. Please install curl first."
    exit 1
fi

echo ""
echo "Step 6: Setting up shell environment..."
echo "--------------------------------------"
# Add uv to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "ðŸ“ Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

echo ""
echo "Step 7: Verifying installation..."
echo "---------------------------------"
# Source the new PATH
export PATH="$HOME/.local/bin:$PATH"

if command_exists uv; then
    echo "âœ… uv successfully installed!"
    uv --version
else
    echo "âŒ uv installation failed. You may need to restart your terminal."
    exit 1
fi

echo ""
echo "Step 8: Installing Python and creating fresh venv..."
echo "----------------------------------------------------"
if [ -f "pyproject.toml" ]; then
    echo "ðŸ“‹ Found pyproject.toml, setting up project..."
    
    # Try to determine Python version from pyproject.toml
    PYTHON_VERSION=$(grep -E 'requires-python.*=' pyproject.toml | sed 's/.*>=\s*"\([0-9]\+\.[0-9]\+\).*/\1/' | head -1)
    
    if [ -z "$PYTHON_VERSION" ]; then
        PYTHON_VERSION="3.11"
        echo "ðŸ No Python version specified, defaulting to $PYTHON_VERSION"
    else
        echo "ðŸ Found Python version requirement: $PYTHON_VERSION"
    fi
    
    echo "ðŸ“¦ Installing Python $PYTHON_VERSION..."
    uv python install "$PYTHON_VERSION"
    
    echo "ðŸ—ï¸  Creating virtual environment..."
    uv venv --python "$PYTHON_VERSION"
    
    echo "ðŸ“š Installing dependencies..."
    uv sync || uv pip install -r requirements.txt || echo "   No requirements.txt found"
else
    echo "ðŸ“‹ No pyproject.toml found, creating basic venv..."
    uv python install 3.11
    uv venv --python 3.11
fi

echo ""
echo "ðŸŽ‰ UV Reset Complete!"
echo "===================="
echo ""
echo "Next steps:"
echo "1. Restart your terminal (or run: source ~/.zshrc)"
echo "2. Test with: uv --version"
echo "3. Test Python: uv run python --version"
echo ""

if [ -f "pyproject.toml" ]; then
    echo "Your project is ready! Try:"
    echo "  uv run python -c 'print(\"Hello from fresh uv!\")'"
fi

echo ""
echo "If you still experience issues, check system logs:"
echo "  log show --predicate 'process == \"python\"' --last 1h"