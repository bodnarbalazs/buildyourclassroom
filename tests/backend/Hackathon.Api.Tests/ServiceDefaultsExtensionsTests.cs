using Hackathon.ServiceDefaults;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using System.Net;

namespace Hackathon.Api.Tests;

public class ServiceDefaultsExtensionsTests
{
    [Fact]
    public void AddDefaultHealthChecks_RegistersHealthCheckService()
    {
        var builder = WebApplication.CreateBuilder();

        builder.AddDefaultHealthChecks();

        var provider = builder.Services.BuildServiceProvider();
        var healthCheckService = provider.GetService<HealthCheckService>();
        Assert.NotNull(healthCheckService);
    }

    [Fact]
    public void ConfigureOpenTelemetry_WithoutOtelEndpoint_DoesNotThrow()
    {
        var builder = WebApplication.CreateBuilder();

        builder.ConfigureOpenTelemetry();

        builder.Services.BuildServiceProvider();
    }

    [Fact]
    public void ConfigureOpenTelemetry_WithOtelEndpoint_DoesNotThrow()
    {
        var builder = WebApplication.CreateBuilder();
        builder.Configuration["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4317";

        builder.ConfigureOpenTelemetry();

        builder.Services.BuildServiceProvider();
    }

    [Fact]
    public void AddServiceDefaults_RegistersAllServices()
    {
        var builder = WebApplication.CreateBuilder();

        builder.AddServiceDefaults();

        var provider = builder.Services.BuildServiceProvider();
        Assert.NotNull(provider.GetService<HealthCheckService>());
    }

    [Fact]
    public async Task MapDefaultEndpoints_MapsHealthEndpoints()
    {
        var builder = WebApplication.CreateBuilder();
        builder.WebHost.UseTestServer();
        builder.AddDefaultHealthChecks();
        var app = builder.Build();
        app.MapDefaultEndpoints();
        await app.StartAsync();

        var client = app.GetTestClient();
        var healthResponse = await client.GetAsync("/health");
        var aliveResponse = await client.GetAsync("/alive");

        Assert.Equal(HttpStatusCode.OK, healthResponse.StatusCode);
        Assert.Equal(HttpStatusCode.OK, aliveResponse.StatusCode);

        await app.StopAsync();
    }
}
