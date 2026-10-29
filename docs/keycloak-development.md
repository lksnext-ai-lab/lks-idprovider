# LKS ID Provider - Development Environment

Run the commands below from the repository root. This environment and its
credentials are for local testing only, not production.

## Quick Start

1. **Start the development environment:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Wait for Keycloak to be ready (about 2-3 minutes):**
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f keycloak
   ```

3. **Access Keycloak Admin Console:**
   - URL: http://localhost:8080
   - Admin credentials: `admin` / `admin123`

## Test Configuration

### Realm: `lks-test`

**Test Users:**
- **Normal User:**
  - Username: `testuser`
  - Password: `password123`
  - Email: `testuser@lks.com`
  - Roles: `user`
  - Client roles: `read`, `write` (PythonServiceTest)

- **Admin User:**
  - Username: `admin`
  - Password: `admin123`
  - Email: `admin@lks.com`
  - Roles: `admin`, `user`
  - Client roles: `admin`, `read`, `write` (PythonServiceTest)

**Test Client:**
- **Client ID:** `PythonServiceTest`
- **Client Secret:** `python-service-secret-123`
- **Service Account:** Enabled
- **Client Credentials Flow:** Enabled
- **Direct Access Grants:** Enabled

### Environment Variables for Testing

```bash
export KEYCLOAK_BASE_URL="http://localhost:8080"
export KEYCLOAK_REALM="lks-test"
export KEYCLOAK_CLIENT_ID="PythonServiceTest"
export KEYCLOAK_CLIENT_SECRET="python-service-secret-123"
```

## Getting Test Tokens

### User Token (testuser)
```bash
curl -X POST \
  http://localhost:8080/realms/lks-test/protocol/openid-connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password' \
  -d 'client_id=PythonServiceTest' \
  -d 'client_secret=python-service-secret-123' \
  -d 'username=testuser' \
  -d 'password=password123'
```

### Admin Token (admin)
```bash
curl -X POST \
  http://localhost:8080/realms/lks-test/protocol/openid-connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password' \
  -d 'client_id=PythonServiceTest' \
  -d 'client_secret=python-service-secret-123' \
  -d 'username=admin' \
  -d 'password=admin123'
```

### Client Credentials Token
```bash
curl -X POST \
  http://localhost:8080/realms/lks-test/protocol/openid-connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials' \
  -d 'client_id=PythonServiceTest' \
  -d 'client_secret=python-service-secret-123'
```

## Development Workflow

1. **Start services:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Install the workspace and run Keycloak tests locally:**
   ```bash
   uv sync --all-packages --all-groups --frozen
   uv run --frozen pytest lks-idprovider-keycloak/tests_keycloak -v
   ```

3. **Stop services:**
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

## Services

- **Keycloak**: http://localhost:8080 (Identity Provider)
- **PostgreSQL**: localhost:5432 (database for Keycloak)

## Troubleshooting

### Keycloak not starting
- Check logs: `docker-compose -f docker-compose.dev.yml logs keycloak`
- Ensure port 8080 is not in use
- Wait for initialization (can take 2-3 minutes)

### Realm not imported
- Check if `keycloak-config/lks-test-realm.json` exists
- Restart Keycloak: `docker-compose -f docker-compose.dev.yml restart keycloak`

### Test tokens not working
- Verify realm is imported correctly
- Check client configuration in Keycloak admin console
- Ensure users exist in the realm
