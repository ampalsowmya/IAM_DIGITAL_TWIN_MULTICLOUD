# Docker on Windows — ports and troubleshooting

## Ports used by this project (host → container)

| Host port | Service    | Container port |
|-----------|------------|----------------|
| **7688**  | Neo4j Bolt | 7687           |
| **7475**  | Neo4j HTTP | 7474           |
| **8000**  | FastAPI    | 8000           |
| **5173**  | Vite UI    | 5173           |
| **8080**  | Nginx      | 80             |

Neo4j Bolt is exposed on **7688** on the host so it does not fight another Neo4j (or tool) using **7687**.

Inside Docker, the backend still connects with **`bolt://neo4j:7687`** (service name + internal port).

---

## PowerShell: what is using a port?

Replace `7687` with the port you care about.

```powershell
# List processes listening on a TCP port
Get-NetTCPConnection -LocalPort 7687 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress, LocalPort, State, OwningProcess

# Owning process details
$pids = (Get-NetTCPConnection -LocalPort 7687 -ErrorAction SilentlyContinue).OwningProcess | Sort-Object -Unique
$pids | ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }

# Classic view (PID in last column)
netstat -ano | findstr ":7687"
```

**If Docker holds the port** (old container):

```powershell
docker ps -a --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
docker stop $(docker ps -aq --filter "publish=7687") 2>$null
```

**If a Windows process holds the port** (PID from `netstat`):

```powershell
Stop-Process -Id <PID> -Force
```

---

## Clean restart (project directory)

```powershell
cd "C:\Users\SOWMYA KARTHIKEYAN\OneDrive\Documents\Desktop\multi-cloud-iam-digital-twin"

docker compose down --remove-orphans
docker compose up -d --build
docker ps
```

---

## Neo4j password

`docker-compose.yml` sets **`NEO4J_AUTH=neo4j/password`**. Your **`backend/.env`** must use the same: **`NEO4J_PASSWORD=password`** and **`NEO4J_URI=bolt://neo4j:7687`** when the backend runs in Compose.

If you change the compose password, update `backend/.env` to match.
