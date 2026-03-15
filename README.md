1. Basic system setup, clone repo, and create virtualenv

SSH to the VPS and run:


# Update and install system packages
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip nginx git curl

# Optionally create a deploy user (recommended)
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG sudo deploy
# Then SSH as deploy or use your existing user

# Clone your repo (example into /opt/schoolsearch)
sudo mkdir -p /opt/schoolsearch
sudo chown $USER:$USER /opt/schoolsearch
git clone 'REPLACE_WITH_YOUR_REPO_URL' /opt/schoolsearch

cd /opt/schoolsearch

# Create venv and install requirements
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

2. Set the GOOGLE_API_KEY securely (systemd EnvironmentFile)
Create an env file:

sudo tee /etc/schoolsearch.env > /dev/null <<'EOF'
GOOGLE_API_KEY=REPLACE_WITH_YOUR_GOOGLE_API_KEY
# (You can add other env vars if needed)
EOF
sudo chmod 600 /etc/schoolsearch.env

3. Create a systemd service to run Gunicorn
Create /etc/systemd/system/schoolsearch.service with the following content:

nano /etc/systemd/system/schoolsearch.service

[Unit]
Description=SchoolSearch Gunicorn Service
After=network.target

[Service]
User=deploy
Group=www-data
EnvironmentFile=/etc/schoolsearch.env
WorkingDirectory=/opt/schoolsearch
# Activate venv and run gunicorn
ExecStart=/opt/schoolsearch/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 run-search:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

Adjust User, WorkingDirectory, and path to venv if different.

4. Start and enable the service

sudo systemctl daemon-reload
sudo systemctl enable --now schoolsearch.service
sudo systemctl status schoolsearch.service

5. Configure nginx as reverse proxy for your domain_name.com
Create nginx site file /etc/nginx/sites-available/schoolsearch:

nano /etc/nginx/sites-available/schoolsearch

# ##################################################################
server {
    listen 80;
    server_name your_domain_name.com;

    root /opt/schoolsearch;
    index index.html;

    location /static/ {
        # If you have static files, adjust path or let Flask/Gunicorn serve
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

# ########################################################################

Enable and test nginx:

sudo ln -s /etc/nginx/sites-available/schoolsearch /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

6. Setup Cloudflare DNS (exact steps)

In Cloudflare DNS panel for your_domain_name.com:
Add an A record:
Name: schoolsearch
IPv4 address: your VPS public IP (e.g., 203.0.113.12)
Proxy status: set to DNS only (grey cloud) for now
Save.

7. Obtain TLS certificate with Certbot (Let's Encrypt)
Install certbot and the nginx plugin:

sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain_name.com

Follow prompts to get cert and let certbot update nginx to use the cert.

8. Optional: If you prefer Cloudflare proxy

After cert is issued, you may enable the Cloudflare proxy (orange cloud). Then in Cloudflare SSL/TLS settings choose "Full (strict)":
For Full (strict) you can use the Let's Encrypt certificate already on your origin. If you want extra safety, you can install a Cloudflare Origin Certificate on the origin and configure nginx with that key instead.
If you enable the proxy and run into issues with HTTP challenge renewal, leave the DNS as DNS-only and use certbot or configure DNS challenge via Cloudflare API (more advanced).

9. Firewall (UFW) allow HTTP/HTTPS and restrict other ports

sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status

10. Verify site
Visit https://schoolsearch.your_domain_name.com/ — you should see your index.html.
Click Search to run run-search endpoint; check schools.json is updated and school-list.html shows distances based on center.
Notes about distance accuracy

Current flow computes distance from the search center (the geocoded/parsed address) to each school's coordinates using the Haversine formula in kilometers. If you used radius in meters (e.g., 200), the search results in schools.json are filtered by that radius in meters at the server and school-list.html shows distances in km.
If you need meter-level precision: change display to meters (server provides distance_m already). Example small tweak in school-list.html to prefer distance_m when available:
Show meters for distances < 1 km and km otherwise.

Renewal

Certbot will create a cron/systemd timer to renew. Test:

sudo certbot renew --dry-run
