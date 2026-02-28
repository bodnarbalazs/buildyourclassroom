using System.IdentityModel.Tokens.Jwt;
using System.Text;
using Hackathon.Api.Endpoints;
using Hackathon.Application;
using Hackathon.Infrastructure;
using Hackathon.Infrastructure.Database;
using Hackathon.Infrastructure.Services.SecretManagement;
using Hackathon.ServiceDefaults;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

builder.AddServiceDefaults();

// Create FileSecretClient early for JWT setup
var secretClient = new FileSecretClient(builder.Configuration);
builder.Services.AddSingleton<ISecretClient>(secretClient);

// OpenAPI
builder.Services.AddOpenApi();

// Application & Infrastructure services
builder.Services.AddApplicationServices();
builder.Services.AddInfrastructureServices(builder.Configuration);

// HttpClient for Python microservice (resolved via Aspire service discovery)
builder.Services.AddHttpClient("microservice", client =>
{
    client.BaseAddress = new Uri("http://microservice");
    client.Timeout = TimeSpan.FromMinutes(2);
});

// Authorization & HttpContextAccessor
builder.Services.AddAuthorization();
builder.Services.AddHttpContextAccessor();

// JWT Authentication
JwtSecurityTokenHandler.DefaultInboundClaimTypeMap.Clear();
var secretKey = secretClient.GetSecretAsync("JwtSettings.SecretKey").GetAwaiter().GetResult();
if (string.IsNullOrEmpty(secretKey))
    throw new InvalidOperationException("JWT Secret Key not found in secrets store.");

var signingKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey));

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = false,
        ValidateAudience = false,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = signingKey,
        RequireSignedTokens = true,
        ValidAlgorithms = [SecurityAlgorithms.HmacSha256],
        ClockSkew = TimeSpan.Zero
    };

    options.Events = new JwtBearerEvents
    {
        OnMessageReceived = context =>
        {
            var token = context.Request.Cookies["accessToken"];
            if (!string.IsNullOrEmpty(token))
                context.Token = token;
            return Task.CompletedTask;
        }
    };
});

// CORS — must AllowCredentials for HttpOnly cookies
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(
                "http://localhost:5069",
                "https://localhost:5069",
                "http://127.0.0.1:5069",
                "https://127.0.0.1:5069")
            .AllowAnyMethod()
            .AllowAnyHeader()
            .AllowCredentials();
    });
});

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapScalarApiReference();
}

app.UseCors();
app.UseAuthentication();
app.UseAuthorization();

app.MapDefaultEndpoints();
app.MapTestEndpoints();
app.MapAuthEndpoints();
app.MapMicroserviceEndpoints();
app.MapSessionEndpoints();
app.MapAgendaEndpoints();

// Auto-migrate with retry (PostGIS image can be slow to initialise)
if (app.Environment.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();

    for (var attempt = 1; attempt <= 10; attempt++)
    {
        try
        {
            db.Database.Migrate();
#pragma warning disable CA1848
            logger.LogInformation("Database migrations applied successfully.");
#pragma warning restore CA1848
            break;
        }
        catch (Exception ex)
        {
            if (attempt >= 10) throw;
#pragma warning disable CA1848
            logger.LogWarning("Database not ready, retrying in 2s ({Attempt}/10)... {Error}",
                attempt, ex.Message);
#pragma warning restore CA1848
            Thread.Sleep(2000);
        }
    }
}

app.Run();
