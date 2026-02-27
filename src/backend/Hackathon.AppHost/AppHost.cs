using Hackathon.Domain.Messages;

var builder = DistributedApplication.CreateBuilder(args);

// ── PostgreSQL (PostGIS-enabled image) ───────────────────────────
// Tag format: "{postgresMajor}-{postgisMajor.minor}". The PG major version
// must match the version that initialised the persistent data volume.
var postgres = builder.AddPostgres("postgres")
    .WithImage("postgis/postgis")
    .WithImageTag("17-3.5")
    .WithLifetime(ContainerLifetime.Persistent)
    .WithDataVolume("hackathon-postgres-data")
    .WithEndpoint("tcp", e => e.Port = 5432)
    .WithPgAdmin(c => c.WithEndpoint("http", e => e.Port = 5050));
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

// ──────────────────────────────────────────────────────────────────
// Core Services
// ──────────────────────────────────────────────────────────────────

var api = builder.AddProject<Projects.Hackathon_Api>("api", launchProfileName: "https")
    .WithReference(hackathonDb)
    .WaitFor(postgres)
    .WithReference(rabbitmq)
    .WaitFor(rabbitmq);

var frontend = builder.AddNpmApp("frontend", frontendWorkingDir, "dev")
    .WithReference(api)
    .WaitFor(api)
    .WithHttpEndpoint(port: 3000, env: "PORT")
    .WithExternalHttpEndpoints()
    .PublishAsDockerFile();

// Python microservice (FastAPI)
var microservice = builder.AddUvicornApp("microservice",
        microserviceWorkingDir,
        "api.main:app")
    .WithUv()
    .WithHttpEndpoint(port: 8000)
    .WithExternalHttpEndpoints();

// Python worker (RabbitMQ consumer)
var worker = builder.AddPythonApp("worker",
        microserviceWorkingDir,
        "workers/add_numbers_worker.py")
    .WithUv()
    .WithReference(rabbitmq)
    .WaitFor(rabbitmq)
    .WithEnvironment("RABBITMQ_HOST", rabbitmq.Resource.PrimaryEndpoint.Property(EndpointProperty.Host))
    .WithEnvironment("RABBITMQ_PORT", rabbitmq.Resource.PrimaryEndpoint.Property(EndpointProperty.Port))
    .WithEnvironment("RABBITMQ_USER", "guest")
    .WithEnvironment("RABBITMQ_PASSWORD", rabbitmq.Resource.PasswordParameter!)
    .WithEnvironment("WORKER_QUEUE", HackathonQueues.AddNumbers);

builder.Build().Run();
