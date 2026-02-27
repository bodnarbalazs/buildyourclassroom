using Hackathon.Application.Auth.Commands.RegisterUser;
using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Shared.Interfaces;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Models.Auth;
using Microsoft.Extensions.Logging;
using Moq;

namespace Hackathon.Application.Tests;

public class RegisterUserCommandHandlerTests
{
    private readonly Mock<IUserRepository> _userRepo = new();
    private readonly Mock<IPasswordHashingService> _hashService = new();
    private readonly Mock<IJwtService> _jwtService = new();
    private readonly Mock<ILogger<RegisterUserCommandHandler>> _logger = new();
    private RegisterUserCommandHandler CreateHandler() =>
        new(_userRepo.Object, _hashService.Object, _jwtService.Object, _logger.Object);

    private static RegisterUserCommand ValidCommand() =>
        new("test@example.com", "validuser", "Abcdefgh123!");

    [Fact]
    public async Task HandleAsync_EmptyEmail_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new RegisterUserCommand("", "validuser", "Abcdefgh123!"));
        Assert.True(result.IsFailure);
        Assert.Contains("Email", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_EmptyUsername_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new RegisterUserCommand("test@example.com", "", "Abcdefgh123!"));
        Assert.True(result.IsFailure);
        Assert.Contains("Username", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_EmptyPassword_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new RegisterUserCommand("test@example.com", "validuser", ""));
        Assert.True(result.IsFailure);
        Assert.Contains("Password", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_InvalidEmail_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new RegisterUserCommand("notanemail", "validuser", "Abcdefgh123!"));
        Assert.True(result.IsFailure);
    }

    [Fact]
    public async Task HandleAsync_InvalidUsername_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new RegisterUserCommand("test@example.com", "admin", "Abcdefgh123!"));
        Assert.True(result.IsFailure);
    }

    [Fact]
    public async Task HandleAsync_InvalidPassword_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new RegisterUserCommand("test@example.com", "validuser", "weak"));
        Assert.True(result.IsFailure);
    }

    [Fact]
    public async Task HandleAsync_DuplicateEmail_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByEmailAsync(It.IsAny<string>()))
            .ReturnsAsync(new User
            {
                Id = "existing", Email = "test@example.com", Username = "existing",
                Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 }
            });

        var result = await handler.HandleAsync(ValidCommand());
        Assert.True(result.IsFailure);
        Assert.Contains("already registered", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_DuplicateUsername_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByEmailAsync(It.IsAny<string>())).ReturnsAsync((User?)null);
        _userRepo.Setup(r => r.GetByUsernameAsync(It.IsAny<string>()))
            .ReturnsAsync(new User
            {
                Id = "existing", Email = "other@example.com", Username = "validuser",
                Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 }
            });

        var result = await handler.HandleAsync(ValidCommand());
        Assert.True(result.IsFailure);
        Assert.Contains("already taken", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_ValidCommand_ReturnsSuccess()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByEmailAsync(It.IsAny<string>())).ReturnsAsync((User?)null);
        _userRepo.Setup(r => r.GetByUsernameAsync(It.IsAny<string>())).ReturnsAsync((User?)null);
        _hashService.Setup(h => h.HashPasswordWithSaltAsync(It.IsAny<string>()))
            .ReturnsAsync(("hash", "salt"));
        _userRepo.Setup(r => r.CreateAsync(It.IsAny<User>())).ReturnsAsync((User u) => u);
        _jwtService.Setup(j => j.GenerateJwtTokenAsync(It.IsAny<User>())).ReturnsAsync("jwt-token");
        _jwtService.Setup(j => j.GenerateRefreshTokenAsync(It.IsAny<User>(), null))
            .ReturnsAsync(new Domain.Models.Auth.RefreshToken { Token = "refresh-token", Expires = DateTime.UtcNow.AddDays(7) });

        var result = await handler.HandleAsync(ValidCommand());
        Assert.True(result.IsSuccess);
        Assert.Equal("jwt-token", result.Value!.AccessToken);
        Assert.Equal("refresh-token", result.Value.RefreshToken.Token);
    }

    [Fact]
    public async Task HandleAsync_RepositoryThrows_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByEmailAsync(It.IsAny<string>()))
            .ThrowsAsync(new InvalidOperationException("DB error"));

        var result = await handler.HandleAsync(ValidCommand());
        Assert.True(result.IsFailure);
        Assert.Contains("error occurred", result.Error!);
    }
}
