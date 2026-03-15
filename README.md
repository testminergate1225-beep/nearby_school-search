
1️⃣ Basic System Setup, Clone Repo, and Create Virtualenv
SSH into your VPS and run:

# Update and install system packages
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip nginx git curl

# (Optional) Create a deploy user
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG sudo deploy
# Then SSH as deploy or continue with your current user

# Clone your repo (example path)
sudo mkdir -p /opt/schoolsearch
sudo chown $USER:$USER /opt/schoolsearch
git clone 'REPLACE_WITH_YOUR_REPO_URL' /opt/schoolsearch

cd /opt/schoolsearch

# Create venv and install requirements
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
