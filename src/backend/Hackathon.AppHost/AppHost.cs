using Hackathon.Domain.Messages;

var builder = DistributedApplication.CreateBuilder(args);

// ── Kubernetes publish target ────────────────────────────────────
builder.AddKubernetesEnvironment("k8s");

// ── PostgreSQL (PostGIS-enabled image) ───────────────────────────
// Tag format: "{postgresMajor}-{postgisMajor.minor}-bookworm". The PG major
// version must match the version that initialised the persistent data volume.
var postgres = builder.AddPostgres("postgres")
    .WithImage("imresamu/postgis")
    .WithImageTag("17-3.5-bookworm")
    .WithLifetime(ContainerLifetime.Persistent)
    .WithDataVolume("hackathon-postgres-data")
    .WithEndpoint("tcp", e => e.Port = 5432)
    .WithPgAdmin(c => c.WithHostPort(5050));
var hackathonDb = postgres.AddDatabase("hackathondb");

// ── RabbitMQ ─────────────────────────────────────────────────────
var rabbitmq = builder.AddRabbitMQ("messaging")
    .WithLifetime(ContainerLifetime.Persistent)
    .WithDataVolume("rabbitmq-data")
    .WithEndpoint("tcp", e => e.Port = 5672)
    .WithManagementPlugin()
    .WithEndpoint("management", e => e.Port = 15672);

// ────────────────────────────────────ż──────────────────────────────
// Resolve working directories
// ──────────────────────────────────────────────────────────────────

var frontendWorkingDir = Path.GetFullPath(
    Path.Combine(builder.AppHostDirectory, "../../frontend"));
var microserviceWorkingDir = Path.GetFullPath(
    Path.Combine(builder.AppHostDirectory, "../../microservices/microservice"));
var dockerDir = Path.GetFullPath(
    Path.Combine(builder.AppHostDirectory, "../../../docker"));

// ── Azure OpenAI ───────────────────────────────────────────────────
var azureOpenAiEndpoint = builder.AddParameter("azure-openai-endpoint");
var azureOpenAiKey = builder.AddParameter("azure-openai-key", secret: true);
var azureOpenAiDeployment = builder.AddParameter("azure-openai-deployment");

var azureOpenAiChatDeployment = builder.AddParameter("azure-openai-chat-deployment");
var azureOpenAiWhisperDeployment = builder.AddParameter("azure-openai-whisper-deployment");

// ──────────────────────────────────────────────────────────────────
// Core Services
// ──────────────────────────────────────────────────────────────────

// Python microservice (FastAPI) — runs in Docker (TF requires Linux)
var microservice = builder.AddDockerfile("microservice",
        microserviceWorkingDir,
        Path.Combine(dockerDir, "microservice.Dockerfile"))
    .WithReference(hackathonDb)
    .WaitFor(postgres)
    .WithHttpEndpoint(targetPort: 8000)
    .WithExternalHttpEndpoints()
    .WithEnvironment("AZURE_OPENAI_ENDPOINT", azureOpenAiEndpoint)
    .WithEnvironment("AZURE_OPENAI_API_KEY", azureOpenAiKey)
    .WithEnvironment("AZURE_OPENAI_DEPLOYMENT_NAME", azureOpenAiDeployment)
    .WithEnvironment("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", azureOpenAiChatDeployment)
    .WithEnvironment("AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME", azureOpenAiWhisperDeployment);

var api = builder.AddProject<Projects.Hackathon_Api>("api", launchProfileName: "https")
    .WithReference(hackathonDb)
    .WaitFor(postgres)
    .WithReference(rabbitmq)
    .WaitFor(rabbitmq)
    .WithReference(microservice.GetEndpoint("http"))
    .WaitFor(microservice);

var frontend = builder.AddNpmApp("frontend", frontendWorkingDir, "dev")
    .WithReference(api)
    .WaitFor(api)
    .WithHttpEndpoint(port: 3000, env: "PORT")
    .WithExternalHttpEndpoints()
    .PublishAsDockerFile();

// Python workers (RabbitMQ consumers) — run in Docker (TF requires Linux)
var addNumbersWorker = builder.AddDockerfile("add-numbers-worker",
        microserviceWorkingDir,
        Path.Combine(dockerDir, "worker.Dockerfile"))
    .WithReference(rabbitmq)
    .WaitFor(rabbitmq)
    .WithEnvironment("RABBITMQ_HOST", rabbitmq.Resource.PrimaryEndpoint.Property(EndpointProperty.Host))
    .WithEnvironment("RABBITMQ_PORT", rabbitmq.Resource.PrimaryEndpoint.Property(EndpointProperty.Port))
    .WithEnvironment("RABBITMQ_USER", "guest")
    .WithEnvironment("RABBITMQ_PASSWORD", rabbitmq.Resource.PasswordParameter!)
    .WithEnvironment("WORKER_QUEUE", HackathonQueues.AddNumbers);

var analyzeSnapshotWorker = builder.AddDockerfile("analyze-snapshot-worker",
        microserviceWorkingDir,
        Path.Combine(dockerDir, "worker.Dockerfile"))
    .WithEntrypoint("uv")
    .WithArgs("run", "python", "workers/analyze_snapshot_worker.py")
    .WithReference(rabbitmq)
    .WaitFor(rabbitmq)
    .WithReference(hackathonDb)
    .WaitFor(postgres)
    .WithEnvironment("RABBITMQ_HOST", rabbitmq.Resource.PrimaryEndpoint.Property(EndpointProperty.Host))
    .WithEnvironment("RABBITMQ_PORT", rabbitmq.Resource.PrimaryEndpoint.Property(EndpointProperty.Port))
    .WithEnvironment("RABBITMQ_USER", "guest")
    .WithEnvironment("RABBITMQ_PASSWORD", rabbitmq.Resource.PasswordParameter!)
    .WithEnvironment("WORKER_QUEUE", HackathonQueues.AnalyzeSnapshot);

builder.Build().Run();
