# Grok-Local Installation Guide

This guide outlines the steps to install and configure Grok-Local, a CLI agent for managing local Git repositories and files, as of February 28, 2025.

## Prerequisites
- **Python**: Version 3.8 or higher (tested with 3.11.0).
- **Git**: Installed and configured for command-line use.
- **Operating System**: Compatible with Windows, macOS, or Linux.
- **Optional**: 
  - Selenium and ChromeDriver for X polling (see X Polling Setup below).
  - A GitHub account and SSH key for repository access.

## Installation Steps
1. **Clone the Repository**:
   - Open a terminal and run:
     ```bash
     git clone git@github.com:imars/grok-local.git
     ```
   - Alternatively, use HTTPS:
     ```bash
     git clone https://github.com/imars/grok-local.git
     ```
   - Navigate to the project directory:
     ```bash
     cd grok-local
     ```

2. **Install Dependencies**:
   - Ensure `pip` is installed for your Python version.
   - Install required Python packages:
     ```bash
     pip install gitpython
     ```
   - If `requirements.txt` exists in the root directory, install additional dependencies:
     ```bash
     pip install -r requirements.txt
     ```
     Note: As of February 28, 2025, `requirements.txt` may be a placeholder; `gitpython` is the primary dependency.

3. **Verify Installation**:
   - Run the agent in interactive mode:
     ```bash
     python grok_checkpoint.py
     ```
   - You should see a `Command:` prompt. Type `version` to confirm:
     ```
     grok-local v0.1
     ```
   - Exit with `exit`.
