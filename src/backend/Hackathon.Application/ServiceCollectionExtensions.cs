using Hackathon.Application.Auth.Commands.LoginUser;
using Hackathon.Application.Auth.Commands.Logout;
using Hackathon.Application.Auth.Commands.RefreshToken;
using Hackathon.Application.Auth.Commands.RegisterUser;
using Microsoft.Extensions.DependencyInjection;

namespace Hackathon.Application;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        services.AddScoped<RegisterUserCommandHandler>();
        services.AddScoped<LoginUserCommandHandler>();
        services.AddScoped<RefreshTokenCommandHandler>();
        services.AddScoped<LogoutCommandHandler>();

        return services;
    }
}
