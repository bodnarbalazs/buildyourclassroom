using Hackathon.Application.Auth.Commands.LoginUser;
using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Shared.Interfaces;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Models.Auth;
using Microsoft.Extensions.Logging;
using Moq;

namespace Hackathon.Application.Tests;

public class LoginUserCommandHandlerTests
{
    private readonly Mock<IUserRepository> _userRepo = new();
    private readonly Mock<IPasswordHashingService> _hashService = new();
    private readonly Mock<IJwtService> _jwtService = new();
    private readonly Mock<ILogger<LoginUserCommandHandler>> _logger = new();
    private LoginUserCommandHandler CreateHandler() =>
        new(_userRepo.Object, _hashService.Object, _jwtService.Object, _logger.Object);

    private static User TestUser() => new()
    {
        Id = "user-1", Email = "test@example.com", Username = "testuser",
        Password = new HashedPassword { Hash = "hash", Salt = "salt", HashVersion = 1, PepperVersion = 1 }
    };

    [Fact]
    public async Task HandleAsync_EmptyEmailOrUsername_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new LoginUserCommand("", "password"));
        Assert.True(result.IsFailure);
        Assert.Contains("required", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_EmptyPassword_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new LoginUserCommand("user@example.com", ""));
        Assert.True(result.IsFailure);
        Assert.Contains("required", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_LoginWithEmail_UserNotFound_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByEmailAsync(It.IsAny<string>())).ReturnsAsync((User?)null);

        var result = await handler.HandleAsync(new LoginUserCommand("user@example.com", "password"));
        Assert.True(result.IsFailure);
        Assert.Contains("Invalid credentials", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_LoginWithUsername_UserNotFound_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByUsernameAsync(It.IsAny<string>())).ReturnsAsync((User?)null);

        var result = await handler.HandleAsync(new LoginUserCommand("testuser", "password"));
        Assert.True(result.IsFailure);
        Assert.Contains("Invalid credentials", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_WrongPassword_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByEmailAsync(It.IsAny<string>())).ReturnsAsync(TestUser());
        _hashService.Setup(h => h.VerifyPasswordWithSaltAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string>()))
            .ReturnsAsync(false);

        var result = await handler.HandleAsync(new LoginUserCommand("test@example.com", "wrong"));
        Assert.True(result.IsFailure);
        Assert.Contains("Invalid credentials", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_ValidLoginWithEmail_ReturnsSuccess()
    {
        var handler = CreateHandler();
        var user = TestUser();
        _userRepo.Setup(r => r.GetByEmailAsync(It.IsAny<string>())).ReturnsAsync(user);
        _hashService.Setup(h => h.VerifyPasswordWithSaltAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string>()))
            .ReturnsAsync(true);
        _userRepo.Setup(r => r.UpdateAsync(It.IsAny<string>(), It.IsAny<User>())).ReturnsAsync(user);
        _jwtService.Setup(j => j.GenerateJwtTokenAsync(It.IsAny<User>())).ReturnsAsync("jwt");
        _jwtService.Setup(j => j.GenerateRefreshTokenAsync(It.IsAny<User>(), null))
            .ReturnsAsync(new Domain.Models.Auth.RefreshToken { Token = "rt", Expires = DateTime.UtcNow.AddDays(7) });

        var result = await handler.HandleAsync(new LoginUserCommand("test@example.com", "correct"));
        Assert.True(result.IsSuccess);
        Assert.Equal("jwt", result.Value!.AccessToken);
    }

    [Fact]
    public async Task HandleAsync_ValidLoginWithUsername_ReturnsSuccess()
    {
        var handler = CreateHandler();
        var user = TestUser();
        _userRepo.Setup(r => r.GetByUsernameAsync("testuser")).ReturnsAsync(user);
        _hashService.Setup(h => h.VerifyPasswordWithSaltAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string>()))
            .ReturnsAsync(true);
        _userRepo.Setup(r => r.UpdateAsync(It.IsAny<string>(), It.IsAny<User>())).ReturnsAsync(user);
        _jwtService.Setup(j => j.GenerateJwtTokenAsync(It.IsAny<User>())).ReturnsAsync("jwt");
        _jwtService.Setup(j => j.GenerateRefreshTokenAsync(It.IsAny<User>(), null))
            .ReturnsAsync(new Domain.Models.Auth.RefreshToken { Token = "rt", Expires = DateTime.UtcNow.AddDays(7) });

        var result = await handler.HandleAsync(new LoginUserCommand("testuser", "correct"));
        Assert.True(result.IsSuccess);
    }

    [Fact]
    public async Task HandleAsync_RepositoryThrows_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByEmailAsync(It.IsAny<string>())).ThrowsAsync(new InvalidOperationException("DB error"));

        var result = await handler.HandleAsync(new LoginUserCommand("test@example.com", "pass"));
        Assert.True(result.IsFailure);
        Assert.Contains("error occurred", result.Error!);
    }
}
