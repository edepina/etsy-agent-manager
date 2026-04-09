# Etsy Agent Manager — GitHub & Project Setup

## Step 1: Create the GitHub Repository

Run these commands on your VPS (or locally, then clone to VPS):

```bash

# Initialise git
git init

# Create the initial structure
mkdir -p app/{models,routes,agents,services,tasks,templates/partials}
mkdir -p static/assets
mkdir -p products
mkdir -p alembic/versions
mkdir -p scripts

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
venv/
.venv/

# Environment
.env
.env.local

# Maxton template (purchased — do not commit)
static/assets/

# Generated products
products/*.pdf
products/*.png
products/*.jpg

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker
pgdata/

# OS
.DS_Store
Thumbs.db

# Alembic
alembic/versions/*.py
!alembic/versions/.gitkeep

# Logs
*.log
celery*.pid
EOF

# Create placeholder files
touch app/__init__.py
touch app/models/__init__.py
touch app/routes/__init__.py
touch app/agents/__init__.py
touch app/services/__init__.py
touch app/tasks/__init__.py
touch static/assets/.gitkeep
touch products/.gitkeep
touch alembic/versions/.gitkeep

# Create .env.example
cat > .env.example << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://edson:yourpassword@db:5432/etsy_agents
DB_PASSWORD=yourpassword

# Redis
REDIS_URL=redis://redis:6379/0

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Etsy API v3
ETSY_API_KEY=your_etsy_api_key
ETSY_SHARED_SECRET=your_etsy_shared_secret

# App
SECRET_KEY=change-this-to-a-random-string
DEBUG=true
EOF

# Initial commit
git add .
git commit -m "Initial project structure"

# Create GitHub repo (using GitHub CLI if installed)
gh repo create etsy-agent-manager --private --source=. --push

# Or manually:
# git remote add origin git@github.com:YOUR_USERNAME/etsy-agent-manager.git
# git push -u origin main
```

## Step 2: Copy Maxton Template

After creating the repo:

```bash
# From your local machine, upload Maxton assets to VPS
scp -r /path/to/maxton/assets/ user@your-vps-ip:/path/to/etsy-agent-manager/static/assets/

# Maxton is in .gitignore since it's a purchased template
# Keep a backup somewhere safe (Google Drive, etc.)
```

## Step 3: Create PROJECT.md

The PROJECT.md file (created separately) goes in the project root and is committed to the repo. This is your single source of truth for the entire build.

```bash
# After creating PROJECT.md
git add PROJECT.md
git commit -m "Add project tracking file"
git push
```
