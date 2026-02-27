using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Shared.Interfaces;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Messages;
using Hackathon.Infrastructure.Database;
using Hackathon.Infrastructure.Database.Repositories;
using Hackathon.Infrastructure.Services.Auth;
using Hackathon.Infrastructure.Services.Messaging;
using Hackathon.Infrastructure.Services.PasswordHashing;
using Hackathon.Infrastructure.Services.SecretManagement;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using RabbitMQ.Client;

namespace Hackathon.Infrastructure;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddInfrastructureServices(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddSingleton<ISecretClient, FileSecretClient>();
        services.AddSingleton<IPasswordHashingService, Argon2IdPasswordHashingService>();
        services.AddScoped<IJwtService, JwtService>();

        services.AddDbContext<AppDbContext>(options =>
        {
            var connectionString = configuration.GetConnectionString("hackathondb")
                                   ?? throw new InvalidOperationException(
                                       "PostgreSQL connection string not found.");

            var dataSourceBuilder = new Npgsql.NpgsqlDataSourceBuilder(connectionString);
            dataSourceBuilder.EnableDynamicJson();
            var dataSource = dataSourceBuilder.Build();

            options.UseNpgsql(dataSource, o => o.EnableRetryOnFailure(5, TimeSpan.FromSeconds(30), null))
                   .UseSnakeCaseNamingConvention();
        });

        services.AddScoped<IUserRepository, PostgresUserRepository>();

        services.AddSingleton<IConnection>(sp =>
        {
            var factory = new ConnectionFactory();
            var cs = configuration.GetConnectionString("messaging");
            if (!string.IsNullOrEmpty(cs))
                factory.Uri = new Uri(cs);
            else
            {
                factory.HostName = "localhost";
                factory.UserName = "guest";
                factory.Password = "guest";
            }
            return factory.CreateConnectionAsync().GetAwaiter().GetResult();
        });

        services.AddSingleton<IAddNumbersClient>(sp =>
            RabbitMqAddNumbersClient.CreateAsync(sp.GetRequiredService<IConnection>())
                .GetAwaiter().GetResult());

        return services;
    }
}
