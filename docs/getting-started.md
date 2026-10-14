# Getting Started with Pokeria

## 1. Prerequisites

Before installing Pokeria, ensure your host system has the following tools installed:

| Requirement | Minimum Version | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Docker & Docker Compose** | Docker 24.0+ | Docker Desktop 4.30+ | Required for one-step containerized deployment |
| **Python** (Local dev) | 3.12+ | Python 3.12 or 3.13 | Managed via `pyenv` or `uv` |
| **Node.js** (Local dev) | 20.0+ | Node 20 LTS or 22 | Required for building Next.js frontend |
| **Rust / Cargo** (Optional) | 1.80+ | Stable channel | Only needed if modifying native solver code |

> [!IMPORTANT]
> **macOS iCloud Warning**: Do **not** clone or place the Pokeria repository inside `~/Desktop` or `~/Documents` if iCloud Drive Desktop Sync is active. iCloud offloads files to the cloud (creating `dataless` APFS stubs) and corrupts `.git` objects. Place your repository in `~/Developer/Pokeria` or `~/Projects/Pokeria`.

---

## 2. Docker Quick Start (Recommended)

The entire Pokeria stack (PostgreSQL database, migration engine, FastAPI backend, background worker, and Next.js frontend) can be launched in seconds with Docker Compose.

### Step 1: Clone the Repository
```bash
git clone https://github.com/cbaezp/Pokeria.git
cd Pokeria
```

### Step 2: Initialize Configuration
Copy the default environment template:
```bash
cp .env.example .env
```

*(By default, `.env.example` binds Web to port `3000`, API to port `8000`, and PostgreSQL to port `5432`. If those ports conflict with existing services on your host, edit `.env` to assign alternatives such as `WEB_PORT=3011`, `API_PORT=8011`, and `DB_PORT=5439`).*

### Step 3: Start the Application Stack
```bash
docker compose up -d
```

### Step 4: Verify Container Health
Check that all 4 long-running services are healthy and the migration runner completed successfully:
```bash
docker compose ps
```
Expected output:
```
NAME                 STATUS                   PORTS
pokerlab-postgres    Up (healthy)             127.0.0.1:5432->5432/tcp
pokerlab-migration   Exited (0) (completed)
pokerlab-api         Up (healthy)             127.0.0.1:8000->8000/tcp
pokerlab-worker      Up
pokerlab-web         Up (healthy)             127.0.0.1:3000->3000/tcp
```

### Step 5: Access the Platform
* **Web Application**: [http://localhost:3000](http://localhost:3000)
* **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **API Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 3. Stopping and Restarting Services

To stop all containers without losing database state:
```bash
docker compose down
```

To view live container logs:
```bash
docker compose logs -f api worker
```

To rebuild container images after modifying source code:
```bash
docker compose build
docker compose up -d
```

> [!CAUTION]
> Never run `docker compose down -v` unless you explicitly want to permanently destroy your local PostgreSQL database volume.

---

## 4. First Steps in the Application

1. **Create or Select a Profile**: When you open [http://localhost:3000](http://localhost:3000), select your profile in the top-right navigation or create a new user profile.
2. **Explore Math Lab**: Navigate to **Learn > Math Lab** to take rapid-fire drills on pot odds, expected value, bluff math, and outs counting.
3. **Practice GTO Drills**: Navigate to **Practice** to drill heads-up postflop spots with real-time feedback and EV loss grading.
4. **Inspect Live Helper**: Navigate to **Live Helper** to test real-time table state reconstruction and strategic decision advice.
