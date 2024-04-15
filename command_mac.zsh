
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python3 and link to python
brew install python3
which python3
sudo ln -s /opt/homebrew/bin/python3 /usr/local/bin/python

# Install pip3 and link to pip
brew install pip3
which pip3 
sudo ln -s /opt/homebrew/bin/pip3 /usr/local/bin/pip

# Install virtual environment and dependencies
python3 -m venv EmailAttachmentAutomation
source EmailAttachmentAutomation/bin/activate
pip install google-api-python-client google-auth pandas openpyxl
pip install google-auth-oauthlib
