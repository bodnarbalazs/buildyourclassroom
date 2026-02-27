using Hackathon.Application;
using Hackathon.Application.Auth.Commands.LoginUser;
using Hackathon.Application.Auth.Commands.Logout;
using Hackathon.Application.Auth.Commands.RefreshToken;
using Hackathon.Application.Auth.Commands.RegisterUser;
using Microsoft.Extensions.DependencyInjection;

namespace Hackathon.Application.Tests;

public class ServiceCollectionExtensionsTests
{
    [Fact]
    public void AddApplicationServices_RegistersAllCommandHandlers()
    {
        var services = new ServiceCollection();

        services.AddApplicationServices();

        Assert.Contains(services, d => d.ServiceType == typeof(RegisterUserCommandHandler) && d.Lifetime == ServiceLifetime.Scoped);
        Assert.Contains(services, d => d.ServiceType == typeof(LoginUserCommandHandler) && d.Lifetime == ServiceLifetime.Scoped);
        Assert.Contains(services, d => d.ServiceType == typeof(RefreshTokenCommandHandler) && d.Lifetime == ServiceLifetime.Scoped);
        Assert.Contains(services, d => d.ServiceType == typeof(LogoutCommandHandler) && d.Lifetime == ServiceLifetime.Scoped);
    }

    [Fact]
    public void AddApplicationServices_ReturnsServiceCollection()
    {
        var services = new ServiceCollection();

        var result = services.AddApplicationServices();

        Assert.Same(services, result);
    }
}
