using System.Security.Claims;
using Hackathon.Application.Auth.Commands.LoginUser;
using Hackathon.Application.Auth.Commands.Logout;
using Hackathon.Application.Auth.Commands.RefreshToken;
using Hackathon.Application.Auth.Commands.RegisterUser;
using Hackathon.Domain.DTOs.Auth;

namespace Hackathon.Api.Endpoints;

public static class AuthEndpoints
{
    private const int TokenExpiryMinutes = 15;

    public static IEndpointRouteBuilder MapAuthEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/auth").WithTags("Authentication");

        group.MapPost("/register", RegisterAsync).AllowAnonymous();
        group.MapPost("/login", LoginAsync).AllowAnonymous();
        group.MapPost("/refresh-token", RefreshTokenAsync).AllowAnonymous();
        group.MapPost("/logout", LogoutAsync).RequireAuthorization();
        group.MapGet("/me", GetMeAsync).RequireAuthorization();

        return routes;
    }

    internal static async Task<IResult> RegisterAsync(
        HttpContext httpContext,
        RegisterUserDto? dto,
        RegisterUserCommandHandler handler,
        IWebHostEnvironment environment)
    {
        if (dto == null || string.IsNullOrEmpty(dto.Email) ||
            string.IsNullOrEmpty(dto.Username) || string.IsNullOrEmpty(dto.Password))
            return Results.BadRequest("Invalid registration data");

        var command = new RegisterUserCommand(dto.Email, dto.Username, dto.Password);
        var result = await handler.HandleAsync(command);

        if (result.IsFailure)
            return Results.BadRequest(result.Error);

        var user = result.Value!.User;
        SetAuthCookies(httpContext, result.Value.AccessToken, result.Value.RefreshToken.Token,
            result.Value.RefreshToken.Expires, environment);

        return Results.Ok(new AuthResponseDto
        {
            ExpiresAt = DateTime.UtcNow.AddMinutes(TokenExpiryMinutes),
            User = MapUserDto(user)
        });
    }

    internal static async Task<IResult> LoginAsync(
        HttpContext httpContext,
        LoginUserDto? dto,
        LoginUserCommandHandler handler,
        IWebHostEnvironment environment)
    {
        if (dto == null || string.IsNullOrEmpty(dto.EmailOrUsername) ||
            string.IsNullOrEmpty(dto.Password))
            return Results.BadRequest("Invalid login data");

        var command = new LoginUserCommand(dto.EmailOrUsername, dto.Password);
        var result = await handler.HandleAsync(command);

        if (result.IsFailure)
            return Results.Unauthorized();

        var user = result.Value!.User;
        SetAuthCookies(httpContext, result.Value.AccessToken, result.Value.RefreshToken.Token,
            result.Value.RefreshToken.Expires, environment);

        return Results.Ok(new AuthResponseDto
        {
            ExpiresAt = DateTime.UtcNow.AddMinutes(TokenExpiryMinutes),
            User = MapUserDto(user)
        });
    }

    internal static async Task<IResult> RefreshTokenAsync(
        HttpContext httpContext,
        RefreshTokenRequestDto? dto,
        RefreshTokenCommandHandler handler,
        IWebHostEnvironment environment)
    {
        if (dto == null || string.IsNullOrEmpty(dto.UserId))
            return Results.BadRequest("Invalid refresh token data");

        var cookieToken = httpContext.Request.Cookies["refreshToken"];
        if (string.IsNullOrEmpty(cookieToken))
            return Results.BadRequest("Missing refresh token");

        var command = new Application.Auth.Commands.RefreshToken.RefreshTokenCommand(dto.UserId, cookieToken);
        var result = await handler.HandleAsync(command);

        if (result.IsFailure)
            return Results.Unauthorized();

        var user = result.Value!.User;
        SetAuthCookies(httpContext, result.Value.AccessToken, result.Value.RefreshToken.Token,
            result.Value.RefreshToken.Expires, environment);

        return Results.Ok(new AuthResponseDto
        {
            ExpiresAt = DateTime.UtcNow.AddMinutes(TokenExpiryMinutes),
            User = MapUserDto(user)
        });
    }

    internal static async Task<IResult> LogoutAsync(
        HttpContext httpContext,
        LogoutCommandHandler handler,
        IWebHostEnvironment environment)
    {
        var userId = httpContext.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (string.IsNullOrEmpty(userId))
            return Results.BadRequest("User ID not found in token");

        if (!httpContext.Request.Cookies.TryGetValue("refreshToken", out var refreshToken) ||
            string.IsNullOrEmpty(refreshToken))
            return Results.BadRequest("Refresh token not found");

        var command = new LogoutCommand(userId, refreshToken);
        var result = await handler.HandleAsync(command);

        if (result.IsFailure)
            return Results.NotFound(result.Error);

        var cookieOptions = new CookieOptions
        {
            HttpOnly = true,
            Secure = true,
            SameSite = environment.IsDevelopment() ? SameSiteMode.None : SameSiteMode.Lax,
            Expires = DateTime.UtcNow.AddDays(-1),
            Path = "/"
        };
        httpContext.Response.Cookies.Delete("refreshToken", cookieOptions);
        httpContext.Response.Cookies.Delete("accessToken", cookieOptions);

        return Results.Ok(new { Message = "Logged out successfully" });
    }

    internal static IResult GetMeAsync(ClaimsPrincipal user)
    {
        var userId = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        var email = user.FindFirst(ClaimTypes.Email)?.Value;
        var username = user.FindFirst("username")?.Value;
        var roles = user.FindAll(ClaimTypes.Role).Select(c => c.Value).ToList();

        if (string.IsNullOrEmpty(userId))
            return Results.BadRequest("User ID not found in token");

        return Results.Ok(new
        {
            Id = userId,
            Email = email,
            Username = username,
            Roles = roles,
            IsAuthenticated = true
        });
    }

    private static void SetAuthCookies(HttpContext httpContext, string accessToken,
        string refreshToken, DateTime refreshExpires, IWebHostEnvironment environment)
    {
        var sameSite = environment.IsDevelopment() ? SameSiteMode.None : SameSiteMode.Lax;

        httpContext.Response.Cookies.Append("accessToken", accessToken, new CookieOptions
        {
            HttpOnly = true,
            Secure = true,
            SameSite = sameSite,
            Expires = DateTime.UtcNow.AddMinutes(TokenExpiryMinutes),
            Path = "/"
        });

        httpContext.Response.Cookies.Append("refreshToken", refreshToken, new CookieOptions
        {
            HttpOnly = true,
            Secure = true,
            SameSite = sameSite,
            Expires = refreshExpires,
            Path = "/"
        });
    }

    private static UserDto MapUserDto(Domain.Models.Auth.User user) => new()
    {
        Id = user.Id,
        Email = user.Email,
        Username = user.Username,
        Roles = user.Roles,
        CreatedAt = user.CreatedAt,
        LastLoginAt = user.LastLoginAt
    };
}
