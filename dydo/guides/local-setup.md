---
area: guides
type: guide
---

# Local Setup

Steps to get the project running after cloning. Covers macOS-specific issues with Docker, secrets, certificates, and frontend dependencies.

---

## Prerequisites

Ensure these are installed before proceeding. See the project `readme.md` in the repository root for links.

- .NET 10 SDK
- Node.js 20+
- Python 3.11+
- Docker Desktop
- uv (`brew install uv`)

---

## 1. Docker CLI on PATH (macOS)

Docker Desktop installs the engine but may not add the CLI to your PATH. Verify:

```bash
docker --version
```

If `command not found`, add Docker's bin directory to your shell profile:

```bash
echo 'export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

> Symlinking into `/usr/local/bin` via `sudo ln -sf` fails on modern macOS due to System Integrity Protection (SIP). Use the PATH approach.

Verify the engine is running:

```bash
docker ps
```

---

## 2. ASP.NET Core Developer Certificate

The Aspire dashboard and API require a trusted dev certificate. Without it you'll see:

> The ASP.NET Core developer certificate is not trusted.

Fix:

```bash
dotnet dev-certs https --trust
```

This adds the certificate to your macOS keychain (prompts for password).

---

## 3. Frontend Dependencies

`node_modules` is not checked in. Without this step the frontend fails with `sh: vite: command not found`.

```bash
cd src/frontend
npm install
```

---

## 4. Secrets Configuration

The API uses a `FileSecretClient` that reads secrets from a JSON file. This file is not in source control.

### Required Secrets

| Key | Used By | Purpose |
|-----|---------|---------|
| `JwtSettings.SecretKey` | `JwtService`, `Program.cs` | Signing JWT tokens (HMAC-SHA256) |
| `Hashing.Pepper` | `Argon2IdPasswordHashingService` | Additional entropy for password hashing |

### Create the File

Generate secure random values:

```bash
openssl rand -base64 48  # For SecretKey
openssl rand -base64 24  # For Pepper
```

Create `src/backend/Hackathon.Api/secrets.json`:

```json
{
  "JwtSettings": {
    "SecretKey": "<generated-value>"
  },
  "Hashing": {
    "Pepper": "<generated-value>"
  }
}
```

### Why This Location?

The `FileSecretClient` resolves the path from `appsettings.json` (`Secrets:FilePath`) relative to the build output directory (`bin/Debug/net10.0/`). It searches several fallback paths, but placing the file directly in the API project directory ensures it's found reliably. See `src/backend/Hackathon.Infrastructure/Services/SecretManagement/FileSecretClient.cs` for the full resolution logic.

Without this file, the API throws: `System.InvalidOperationException: JWT Secret Key not found in secrets store.`

---

## 5. Run the Application

```bash
dotnet run --project src/backend/Hackathon.AppHost
```

This launches the Aspire dashboard with all services (API, Frontend, Microservice).

---

## Quick Verification Checklist

| Step | Command | Expected |
|------|---------|----------|
| Docker CLI | `docker --version` | Version string |
| Docker engine | `docker ps` | Empty table (no error) |
| .NET cert | `dotnet dev-certs https --check --trust` | No warnings |
| Frontend deps | `ls src/frontend/node_modules` | Directory exists |
| Secrets | `cat src/backend/Hackathon.Api/secrets.json` | JSON with values |
| uv | `uv --version` | Version string |

---

## Related

- [Coding Standards](./coding-standards.md) — Code conventions
- [Architecture](../understand/architecture.md) — Project structure
