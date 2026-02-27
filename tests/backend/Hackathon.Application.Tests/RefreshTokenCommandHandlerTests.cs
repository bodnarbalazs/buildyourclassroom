using Hackathon.Application.Auth.Commands.RefreshToken;
using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Shared.Interfaces;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Models.Auth;
using Microsoft.Extensions.Logging;
using Moq;

namespace Hackathon.Application.Tests;

public class RefreshTokenCommandHandlerTests
{
    private readonly Mock<IUserRepository> _userRepo = new();
    private readonly Mock<IJwtService> _jwtService = new();
    private readonly Mock<ILogger<RefreshTokenCommandHandler>> _logger = new();
    private RefreshTokenCommandHandler CreateHandler() =>
        new(_userRepo.Object, _jwtService.Object, _logger.Object);

    [Fact]
    public async Task HandleAsync_EmptyUserId_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new RefreshTokenCommand("", "token"));
        Assert.True(result.IsFailure);
        Assert.Contains("User ID", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_EmptyToken_ReturnsFailure()
    {
        var handler = CreateHandler();
        var result = await handler.HandleAsync(new RefreshTokenCommand("user-1", ""));
        Assert.True(result.IsFailure);
        Assert.Contains("Token", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_UserNotFound_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync((User?)null);

        var result = await handler.HandleAsync(new RefreshTokenCommand("user-1", "token"));
        Assert.True(result.IsFailure);
        Assert.Contains("Invalid refresh token", result.Error!);
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

        var result = await handler.HandleAsync(new RefreshTokenCommand("user-1", "nonexistent"));
        Assert.True(result.IsFailure);
        Assert.Contains("Invalid refresh token", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_ExpiredToken_ReturnsFailure()
    {
        var handler = CreateHandler();
        var user = new User
        {
            Id = "user-1", Email = "a@b.com", Username = "test",
            Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 },
            RefreshTokens = [new() { Token = "old-token", Expires = DateTime.UtcNow.AddDays(-1) }]
        };
        _userRepo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync(user);

        var result = await handler.HandleAsync(new RefreshTokenCommand("user-1", "old-token"));
        Assert.True(result.IsFailure);
        Assert.Contains("Invalid refresh token", result.Error!);
    }

    [Fact]
    public async Task HandleAsync_RevokedToken_ReturnsFailure()
    {
        var handler = CreateHandler();
        var user = new User
        {
            Id = "user-1", Email = "a@b.com", Username = "test",
            Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 },
            RefreshTokens = [new() { Token = "revoked-token", Expires = DateTime.UtcNow.AddDays(7), IsRevoked = true }]
        };
        _userRepo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync(user);

        var result = await handler.HandleAsync(new RefreshTokenCommand("user-1", "revoked-token"));
        Assert.True(result.IsFailure);
    }

    [Fact]
    public async Task HandleAsync_ValidToken_ReturnsSuccess()
    {
        var handler = CreateHandler();
        var user = new User
        {
            Id = "user-1", Email = "a@b.com", Username = "test",
            Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 },
            RefreshTokens = [new() { Token = "valid-token", Expires = DateTime.UtcNow.AddDays(7) }]
        };
        _userRepo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync(user);
        _userRepo.Setup(r => r.UpdateAsync(It.IsAny<string>(), It.IsAny<User>())).ReturnsAsync(user);
        _jwtService.Setup(j => j.GenerateJwtTokenAsync(It.IsAny<User>())).ReturnsAsync("new-jwt");
        _jwtService.Setup(j => j.GenerateRefreshTokenAsync(It.IsAny<User>(), null))
            .ReturnsAsync(new Domain.Models.Auth.RefreshToken { Token = "new-rt", Expires = DateTime.UtcNow.AddDays(7) });

        var result = await handler.HandleAsync(new RefreshTokenCommand("user-1", "valid-token"));
        Assert.True(result.IsSuccess);
        Assert.Equal("new-jwt", result.Value!.AccessToken);
        Assert.True(user.RefreshTokens[0].IsRevoked);
    }

    [Fact]
    public async Task HandleAsync_RepositoryThrows_ReturnsFailure()
    {
        var handler = CreateHandler();
        _userRepo.Setup(r => r.GetByIdAsync(It.IsAny<string>())).ThrowsAsync(new InvalidOperationException("DB error"));

        var result = await handler.HandleAsync(new RefreshTokenCommand("user-1", "token"));
        Assert.True(result.IsFailure);
        Assert.Contains("error occurred", result.Error!);
    }
}
