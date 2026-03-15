
1️⃣ Basic System Setup, Clone Repo, and Create Virtualenv
SSH into your VPS and run:

Update and install system packages
- sudo apt update
- sudo apt upgrade -y
- sudo apt install -y python3 python3-venv python3-pip nginx git curl

(Optional) Create a deploy user
- sudo adduser --disabled-password --gecos "" deploy
- sudo usermod -aG sudo deploy
- Then SSH as deploy or continue with your current user

Clone your repo (example path)
- sudo mkdir -p /opt/schoolsearch
- sudo chown $USER:$USER /opt/schoolsearch
- git clone 'REPLACE_WITH_YOUR_REPO_URL' /opt/schoolsearch
- cd /opt/schoolsearch

Create venv and install requirements
- python3 -m venv .venv
- source .venv/bin/activate
- pip install --upgrade pip
- pip install -r requirements.txt

2️⃣ Set the GOOGLE_API_KEY Securely (systemd EnvironmentFile)
Create an environment file:
- sudo tee /etc/schoolsearch.env > /dev/null <<'EOF'
GOOGLE_API_KEY=REPLACE_WITH_YOUR_GOOGLE_API_KEY
Add other environment variables here if needed
EOF
- sudo chmod 600 /etc/schoolsearch.env



3️⃣ Create a systemd Service for Gunicorn
Create the service file:
- sudo nano /etc/systemd/system/schoolsearch.service

Paste:
-
[Unit]
Description=SchoolSearch Gunicorn Service
After=network.target
[Service]
User=deploy
Group=www-data
EnvironmentFile=/etc/schoolsearch.env
WorkingDirectory=/opt/schoolsearch
ExecStart=/opt/schoolsearch/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 run-search:app
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
-

Adjust User, WorkingDirectory, and venv path if needed.

4️⃣ Start and Enable the Service
- sudo systemctl daemon-reload
- sudo systemctl enable --now schoolsearch.service
- sudo systemctl status schoolsearch.service



5️⃣ Configure Nginx Reverse Proxy
Create the site config:
- sudo nano /etc/nginx/sites-available/schoolsearch


Paste:
- 
server {
    listen 80;
    server_name your_domain_name.com;

    root /opt/schoolsearch;
    index index.html;

    location /static/ {
        alias /opt/schoolsearch/static/;
        try_files $uri =404;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 90;
    }
}
- 

Enable and test:
- sudo ln -s /etc/nginx/sites-available/schoolsearch /etc/nginx/sites-enabled/
- sudo nginx -t
- sudo systemctl restart nginx


6️⃣ Cloudflare DNS Setup
In Cloudflare DNS:
|  |  | 
|  |  | 
|  |  | 
|  |  | 
|  |  | 



7️⃣ Obtain TLS Certificate (Certbot)
- sudo apt install -y certbot python3-certbot-nginx
- sudo certbot --nginx -d your_domain_name.com


Follow prompts to install HTTPS automatically.

8️⃣ Optional: Enable Cloudflare Proxy
After cert is issued:
- Turn on the orange cloud (proxy)
- Set SSL/TLS mode to Full (strict)
If HTTP challenge renewal fails, switch back to DNS-only or configure DNS challenge via Cloudflare API.

9️⃣ Firewall (UFW)
- sudo ufw allow 'Nginx Full'
- sudo ufw enable
- sudo ufw status


🔟 Verify Deployment
Visit:
https://schoolsearch.your_domain_name.com/


You should see:
- index.html loads
- Search works
- schools.json updates
- school-list.html shows distances

📏 Notes on Distance Accuracy
- Server computes distance using Haversine formula in kilometers.
- Radius filtering uses meters.
- Server already provides distance_m.
Suggested UI logic:
- Show meters for distances < 1 km
- Show kilometers otherwise

🔄 Certificate Renewal
Certbot auto-renews via systemd timer.
Test renewal:
sudo certbot renew --dry-run

