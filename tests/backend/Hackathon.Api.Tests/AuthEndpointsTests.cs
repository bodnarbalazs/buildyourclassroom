using System.Security.Claims;
using Hackathon.Api.Endpoints;
using Hackathon.Application.Auth.Commands.LoginUser;
using Hackathon.Application.Auth.Commands.Logout;
using Hackathon.Application.Auth.Commands.RefreshToken;
using Hackathon.Application.Auth.Commands.RegisterUser;
using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Shared.Interfaces;
using Hackathon.Application.Shared.Models;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.DTOs.Auth;
using Hackathon.Domain.Models.Auth;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Moq;

namespace Hackathon.Api.Tests;

public class AuthEndpointsTests
{
    private static DefaultHttpContext CreateHttpContext()
    {
        var context = new DefaultHttpContext();
        return context;
    }

    private static Mock<IWebHostEnvironment> CreateEnv(bool isDevelopment = true)
    {
        var env = new Mock<IWebHostEnvironment>();
        env.Setup(e => e.EnvironmentName).Returns(isDevelopment ? "Development" : "Production");
        return env;
    }

    private static RegisterUserCommandHandler CreateRegisterHandler(
        Mock<IUserRepository>? userRepo = null,
        Mock<IPasswordHashingService>? hashService = null,
        Mock<IJwtService>? jwtService = null)
    {
        return new RegisterUserCommandHandler(
            (userRepo ?? new Mock<IUserRepository>()).Object,
            (hashService ?? new Mock<IPasswordHashingService>()).Object,
            (jwtService ?? new Mock<IJwtService>()).Object,
            new Mock<ILogger<RegisterUserCommandHandler>>().Object);
    }

    private static LoginUserCommandHandler CreateLoginHandler(
        Mock<IUserRepository>? userRepo = null,
        Mock<IPasswordHashingService>? hashService = null,
        Mock<IJwtService>? jwtService = null)
    {
        return new LoginUserCommandHandler(
            (userRepo ?? new Mock<IUserRepository>()).Object,
            (hashService ?? new Mock<IPasswordHashingService>()).Object,
            (jwtService ?? new Mock<IJwtService>()).Object,
            new Mock<ILogger<LoginUserCommandHandler>>().Object);
    }

    private static RefreshTokenCommandHandler CreateRefreshHandler(
        Mock<IUserRepository>? userRepo = null,
        Mock<IJwtService>? jwtService = null)
    {
        return new RefreshTokenCommandHandler(
            (userRepo ?? new Mock<IUserRepository>()).Object,
            (jwtService ?? new Mock<IJwtService>()).Object,
            new Mock<ILogger<RefreshTokenCommandHandler>>().Object);
    }

    private static LogoutCommandHandler CreateLogoutHandler(Mock<IUserRepository>? userRepo = null)
    {
        return new LogoutCommandHandler(
            (userRepo ?? new Mock<IUserRepository>()).Object,
            new Mock<ILogger<LogoutCommandHandler>>().Object);
    }

    private static (Mock<IUserRepository> repo, Mock<IPasswordHashingService> hash, Mock<IJwtService> jwt) SetupSuccessfulRegister()
    {
        var repo = new Mock<IUserRepository>();
        var hash = new Mock<IPasswordHashingService>();
        var jwt = new Mock<IJwtService>();

        repo.Setup(r => r.GetByEmailAsync(It.IsAny<string>())).ReturnsAsync((User?)null);
        repo.Setup(r => r.GetByUsernameAsync(It.IsAny<string>())).ReturnsAsync((User?)null);
        hash.Setup(h => h.HashPasswordWithSaltAsync(It.IsAny<string>())).ReturnsAsync(("hash", "salt"));
        repo.Setup(r => r.CreateAsync(It.IsAny<User>())).ReturnsAsync((User u) => u);
        jwt.Setup(j => j.GenerateJwtTokenAsync(It.IsAny<User>())).ReturnsAsync("access-token");
        jwt.Setup(j => j.GenerateRefreshTokenAsync(It.IsAny<User>(), null))
            .ReturnsAsync(new RefreshToken { Token = "refresh-token", Expires = DateTime.UtcNow.AddDays(7) });

        return (repo, hash, jwt);
    }

    private static (Mock<IUserRepository> repo, Mock<IPasswordHashingService> hash, Mock<IJwtService> jwt) SetupSuccessfulLogin()
    {
        var repo = new Mock<IUserRepository>();
        var hash = new Mock<IPasswordHashingService>();
        var jwt = new Mock<IJwtService>();

        var user = new User
        {
            Id = "user-1", Email = "test@example.com", Username = "testuser",
            Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 }
        };
        repo.Setup(r => r.GetByEmailAsync(It.IsAny<string>())).ReturnsAsync(user);
        hash.Setup(h => h.VerifyPasswordWithSaltAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string>())).ReturnsAsync(true);
        repo.Setup(r => r.UpdateAsync(It.IsAny<string>(), It.IsAny<User>())).ReturnsAsync(user);
        jwt.Setup(j => j.GenerateJwtTokenAsync(It.IsAny<User>())).ReturnsAsync("access-token");
        jwt.Setup(j => j.GenerateRefreshTokenAsync(It.IsAny<User>(), null))
            .ReturnsAsync(new RefreshToken { Token = "refresh-token", Expires = DateTime.UtcNow.AddDays(7) });

        return (repo, hash, jwt);
    }

    #region RegisterAsync

    [Fact]
    public async Task RegisterAsync_NullDto_ReturnsBadRequest()
    {
        var handler = CreateRegisterHandler();
        var result = await AuthEndpoints.RegisterAsync(CreateHttpContext(), null, handler, CreateEnv().Object);
        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.BadRequest<string>>(result);
    }

    [Fact]
    public async Task RegisterAsync_EmptyFields_ReturnsBadRequest()
    {
        var handler = CreateRegisterHandler();
        var dto = new RegisterUserDto { Email = "", Username = "", Password = "" };
        var result = await AuthEndpoints.RegisterAsync(CreateHttpContext(), dto, handler, CreateEnv().Object);
        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.BadRequest<string>>(result);
    }

    [Fact]
    public async Task RegisterAsync_HandlerFailure_ReturnsBadRequest()
    {
        var repo = new Mock<IUserRepository>();
        repo.Setup(r => r.GetByEmailAsync(It.IsAny<string>()))
            .ReturnsAsync(new User
            {
                Id = "x", Email = "test@example.com", Username = "x",
                Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 }
            });
        var handler = CreateRegisterHandler(repo);
        var dto = new RegisterUserDto { Email = "test@example.com", Username = "validuser", Password = "Abcdefgh123!" };

        var result = await AuthEndpoints.RegisterAsync(CreateHttpContext(), dto, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.BadRequest<string>>(result);
    }

    [Fact]
    public async Task RegisterAsync_Success_ReturnsOk()
    {
        var (repo, hash, jwt) = SetupSuccessfulRegister();
        var handler = CreateRegisterHandler(repo, hash, jwt);
        var dto = new RegisterUserDto { Email = "new@example.com", Username = "newuser", Password = "Abcdefgh123!" };

        var result = await AuthEndpoints.RegisterAsync(CreateHttpContext(), dto, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.Ok<AuthResponseDto>>(result);
    }

    #endregion

    #region LoginAsync

    [Fact]
    public async Task LoginAsync_NullDto_ReturnsBadRequest()
    {
        var handler = CreateLoginHandler();
        var result = await AuthEndpoints.LoginAsync(CreateHttpContext(), null, handler, CreateEnv().Object);
        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.BadRequest<string>>(result);
    }

    [Fact]
    public async Task LoginAsync_HandlerFailure_ReturnsUnauthorized()
    {
        var repo = new Mock<IUserRepository>();
        repo.Setup(r => r.GetByEmailAsync(It.IsAny<string>())).ReturnsAsync((User?)null);
        var handler = CreateLoginHandler(repo);
        var dto = new LoginUserDto { EmailOrUsername = "nobody@example.com", Password = "password" };

        var result = await AuthEndpoints.LoginAsync(CreateHttpContext(), dto, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.UnauthorizedHttpResult>(result);
    }

    [Fact]
    public async Task LoginAsync_Success_ReturnsOk()
    {
        var (repo, hash, jwt) = SetupSuccessfulLogin();
        var handler = CreateLoginHandler(repo, hash, jwt);
        var dto = new LoginUserDto { EmailOrUsername = "test@example.com", Password = "correct" };

        var result = await AuthEndpoints.LoginAsync(CreateHttpContext(), dto, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.Ok<AuthResponseDto>>(result);
    }

    #endregion

    #region RefreshTokenAsync

    [Fact]
    public async Task RefreshTokenAsync_NullDto_ReturnsBadRequest()
    {
        var handler = CreateRefreshHandler();
        var result = await AuthEndpoints.RefreshTokenAsync(CreateHttpContext(), null, handler, CreateEnv().Object);
        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.BadRequest<string>>(result);
    }

    [Fact]
    public async Task RefreshTokenAsync_MissingCookie_ReturnsBadRequest()
    {
        var handler = CreateRefreshHandler();
        var dto = new RefreshTokenRequestDto { UserId = "user-1" };

        var result = await AuthEndpoints.RefreshTokenAsync(CreateHttpContext(), dto, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.BadRequest<string>>(result);
    }

    [Fact]
    public async Task RefreshTokenAsync_HandlerFailure_ReturnsUnauthorized()
    {
        var repo = new Mock<IUserRepository>();
        repo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync((User?)null);
        var handler = CreateRefreshHandler(repo);

        var context = CreateHttpContext();
        context.Request.Headers["Cookie"] = "refreshToken=some-token";
        var dto = new RefreshTokenRequestDto { UserId = "user-1" };

        var result = await AuthEndpoints.RefreshTokenAsync(context, dto, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.UnauthorizedHttpResult>(result);
    }

    [Fact]
    public async Task RefreshTokenAsync_Success_ReturnsOk()
    {
        var repo = new Mock<IUserRepository>();
        var jwt = new Mock<IJwtService>();
        var user = new User
        {
            Id = "user-1", Email = "a@b.com", Username = "test",
            Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 },
            RefreshTokens = [new RefreshToken { Token = "valid-token", Expires = DateTime.UtcNow.AddDays(7) }]
        };
        repo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync(user);
        repo.Setup(r => r.UpdateAsync(It.IsAny<string>(), It.IsAny<User>())).ReturnsAsync(user);
        jwt.Setup(j => j.GenerateJwtTokenAsync(It.IsAny<User>())).ReturnsAsync("new-jwt");
        jwt.Setup(j => j.GenerateRefreshTokenAsync(It.IsAny<User>(), null))
            .ReturnsAsync(new RefreshToken { Token = "new-rt", Expires = DateTime.UtcNow.AddDays(7) });
        var handler = CreateRefreshHandler(repo, jwt);

        var context = CreateHttpContext();
        context.Request.Headers["Cookie"] = "refreshToken=valid-token";
        var dto = new RefreshTokenRequestDto { UserId = "user-1" };

        var result = await AuthEndpoints.RefreshTokenAsync(context, dto, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.Ok<AuthResponseDto>>(result);
    }

    #endregion

    #region LogoutAsync

    [Fact]
    public async Task LogoutAsync_NoUserIdClaim_ReturnsBadRequest()
    {
        var handler = CreateLogoutHandler();
        var context = CreateHttpContext();
        context.User = new ClaimsPrincipal(new ClaimsIdentity());

        var result = await AuthEndpoints.LogoutAsync(context, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.BadRequest<string>>(result);
    }

    [Fact]
    public async Task LogoutAsync_NoCookie_ReturnsBadRequest()
    {
        var handler = CreateLogoutHandler();
        var context = CreateHttpContext();
        context.User = new ClaimsPrincipal(new ClaimsIdentity(
            [new Claim(ClaimTypes.NameIdentifier, "user-1")], "test"));

        var result = await AuthEndpoints.LogoutAsync(context, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.BadRequest<string>>(result);
    }

    [Fact]
    public async Task LogoutAsync_HandlerFailure_ReturnsNotFound()
    {
        var repo = new Mock<IUserRepository>();
        repo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync((User?)null);
        var handler = CreateLogoutHandler(repo);

        var context = CreateHttpContext();
        context.User = new ClaimsPrincipal(new ClaimsIdentity(
            [new Claim(ClaimTypes.NameIdentifier, "user-1")], "test"));
        context.Request.Headers["Cookie"] = "refreshToken=the-token";

        var result = await AuthEndpoints.LogoutAsync(context, handler, CreateEnv().Object);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.NotFound<string>>(result);
    }

    [Fact]
    public async Task LogoutAsync_Success_Development_ReturnsOk()
    {
        var repo = new Mock<IUserRepository>();
        var user = new User
        {
            Id = "user-1", Email = "a@b.com", Username = "test",
            Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 },
            RefreshTokens = [new RefreshToken { Token = "the-token", Expires = DateTime.UtcNow.AddDays(7) }]
        };
        repo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync(user);
        repo.Setup(r => r.UpdateAsync(It.IsAny<string>(), It.IsAny<User>())).ReturnsAsync(user);
        var handler = CreateLogoutHandler(repo);

        var context = CreateHttpContext();
        context.User = new ClaimsPrincipal(new ClaimsIdentity(
            [new Claim(ClaimTypes.NameIdentifier, "user-1")], "test"));
        context.Request.Headers["Cookie"] = "refreshToken=the-token";

        var result = await AuthEndpoints.LogoutAsync(context, handler, CreateEnv(isDevelopment: true).Object);

        var statusResult = Assert.IsAssignableFrom<Microsoft.AspNetCore.Http.IStatusCodeHttpResult>(result);
        Assert.Equal(200, statusResult.StatusCode);
    }

    [Fact]
    public async Task LogoutAsync_Success_Production_ReturnsOk()
    {
        var repo = new Mock<IUserRepository>();
        var user = new User
        {
            Id = "user-1", Email = "a@b.com", Username = "test",
            Password = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 },
            RefreshTokens = [new RefreshToken { Token = "the-token", Expires = DateTime.UtcNow.AddDays(7) }]
        };
        repo.Setup(r => r.GetByIdAsync("user-1")).ReturnsAsync(user);
        repo.Setup(r => r.UpdateAsync(It.IsAny<string>(), It.IsAny<User>())).ReturnsAsync(user);
        var handler = CreateLogoutHandler(repo);

        var context = CreateHttpContext();
        context.User = new ClaimsPrincipal(new ClaimsIdentity(
            [new Claim(ClaimTypes.NameIdentifier, "user-1")], "test"));
        context.Request.Headers["Cookie"] = "refreshToken=the-token";

        var result = await AuthEndpoints.LogoutAsync(context, handler, CreateEnv(isDevelopment: false).Object);

        var statusResult = Assert.IsAssignableFrom<Microsoft.AspNetCore.Http.IStatusCodeHttpResult>(result);
        Assert.Equal(200, statusResult.StatusCode);
    }

    #endregion

    #region GetMeAsync

    [Fact]
    public void GetMeAsync_NoUserIdClaim_ReturnsBadRequest()
    {
        var user = new ClaimsPrincipal(new ClaimsIdentity());

        var result = AuthEndpoints.GetMeAsync(user);

        Assert.IsType<Microsoft.AspNetCore.Http.HttpResults.BadRequest<string>>(result);
    }

    [Fact]
    public void GetMeAsync_ValidClaims_ReturnsOk()
    {
        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, "user-1"),
            new Claim(ClaimTypes.Email, "test@example.com"),
            new Claim("username", "testuser"),
            new Claim(ClaimTypes.Role, "User"),
        };
        var user = new ClaimsPrincipal(new ClaimsIdentity(claims, "test"));

        var result = AuthEndpoints.GetMeAsync(user);

        var statusResult = Assert.IsAssignableFrom<Microsoft.AspNetCore.Http.IStatusCodeHttpResult>(result);
        Assert.Equal(200, statusResult.StatusCode);
    }

    #endregion
}
