using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Shared.Interfaces;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Messages;
using Hackathon.Infrastructure.Database;
using Hackathon.Infrastructure.Database.Repositories;
using Hackathon.Infrastructure.Services.Auth;
using Hackathon.Infrastructure.Services.PasswordHashing;
using Hackathon.Infrastructure.Services.SecretManagement;
using MassTransit;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Hackathon.Infrastructure;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddInfrastructureServices(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        // Secret client
        services.AddSingleton<ISecretClient, FileSecretClient>();

        // Password hashing
        services.AddSingleton<IPasswordHashingService, Argon2IdPasswordHashingService>();

        // JWT service
        services.AddScoped<IJwtService, JwtService>();

        // PostgreSQL DbContext
        services.AddDbContext<AppDbContext>(options =>
        {
            var connectionString = configuration.GetConnectionString("hackathondb")
                                   ?? throw new InvalidOperationException(
                                       "PostgreSQL connection string 'hackathondb' not found.");

            var dataSourceBuilder = new Npgsql.NpgsqlDataSourceBuilder(connectionString);
            dataSourceBuilder.EnableDynamicJson();
            var dataSource = dataSourceBuilder.Build();

            options.UseNpgsql(dataSource, npgsqlOptions =>
                   {
                       npgsqlOptions.EnableRetryOnFailure(
                           maxRetryCount: 5,
                           maxRetryDelay: TimeSpan.FromSeconds(30),
                           errorCodesToAdd: null);
                   })
                   .UseSnakeCaseNamingConvention();
        });

        // Repositories
        services.AddScoped<IUserRepository, PostgresUserRepository>();

        // MassTransit with RabbitMQ
        services.AddMassTransit(x =>
        {
            x.AddRequestClient<AddNumbersCommand>(
                new Uri($"queue:{HackathonQueues.AddNumbers}"),
                timeout: TimeSpan.FromSeconds(30));

            x.UsingRabbitMq((context, cfg) =>
            {
                var rabbitMqConnectionString = configuration.GetConnectionString("messaging");

                if (!string.IsNullOrEmpty(rabbitMqConnectionString))
                {
                    cfg.Host(new Uri(rabbitMqConnectionString));
                }
                else
                {
                    cfg.Host("localhost", "/", h =>
                    {
                        h.Username("guest");
                        h.Password("guest");
                    });
                }

                cfg.ConfigureEndpoints(context);
            });
        });

        return services;
    }
}
