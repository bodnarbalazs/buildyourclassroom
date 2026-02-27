using Hackathon.Application.Auth.Commands.Logout;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Models.Auth;
using Microsoft.Extensions.Logging;
using Moq;

namespace Hackathon.Application.Tests;

public class LogoutCommandHandlerTests
{
    private readonly Mock<IUserRepository> _userRepo = new();
    private readonly Mock<ILogger<LogoutCommandHandler>> _logger = new();
    private LogoutCommandHandler CreateHandler() => new(_userRepo.Object, _logger.Object);

    [Fact]
    public async Task HandleAsync_EmptyUserId_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new LogoutCommand("", "token"));
        Assert.True(result.IsFailure);
        Assert.Contains("User ID", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_EmptyToken_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new LogoutCommand("user-1", ""));
        Assert.True(result.IsFailure);
        Assert.Contains("Token", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_UserNotFound_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync((User?)null);

        var result = await handler.HandleAsync(new LogoutCommand("user-1", "token"));
        Assert.True(result.IsFailure);
        Assert.Contains("User not found", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_TokenNotFound_ReturnsFailure()
    {
        var handler = CreateHandler();
        var user = new User
        {
            Id = "user-1", Email = "a@b.com", Username = "test",
            Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 },
            RefreshTokens = []
        };
        _userRepo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync(user);

        var result = await handler.HandleAsync(new LogoutCommand("user-1", "nonexistent"));
        Assert.True(result.IsFailure);
        Assert.Contains("Refresh token not found", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_ValidLogout_ReturnsSuccess()
    {
        var handler = CreateHandler();
        var user = new User
        {
            Id = "user-1", Email = "a@b.com", Username = "test",
            Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 },
            RefreshTokens = [new() { Token = "the-token", Expires = DateTime.UtcNow.AddDays(7) }]
        };
        _userRepo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync(user);
        _userRepo.Setup(r => r.UpdateAsync(It.IsAny<string>(), It.IsAny<User>())).ReturnsAsync(user);

        var result = await handler.HandleAsync(new LogoutCommand("user-1", "the-token"));
        Assert.True(result.IsSuccess);
        Assert.True(user.RefreshTokens[0].IsRevoked);
    }

    [Fact]
    public async Task HandleAsync_RepositoryThrows_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByIdAsync(It.IsAny<string>())).ThrowsAsync(new InvalidOperationException("DB error"));

        var result = await handler.HandleAsync(new LogoutCommand("user-1", "token"));
        Assert.True(result.IsFailure);
        Assert.Contains("error occurred", result.Error!);
    }
}
