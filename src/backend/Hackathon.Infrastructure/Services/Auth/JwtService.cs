using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Models.Auth;
using Hackathon.Infrastructure.Services.SecretManagement;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.IdentityModel.Tokens;

namespace Hackathon.Infrastructure.Services.Auth;

public class JwtService : IJwtService
{
    private readonly IUserRepository _userRepository;
    private readonly IConfiguration _configuration;
    private readonly ILogger<JwtService> _logger;
    private readonly ISecretClient _secretClient;

    public JwtService(
        IUserRepository userRepository,
        IConfiguration configuration,
        ILogger<JwtService> logger,
        ISecretClient secretClient)
    {
        _userRepository = userRepository;
        _configuration = configuration;
        _logger = logger;
        _secretClient = secretClient;
    }

    public async Task<string> GenerateJwtTokenAsync(User user)
    {
        ArgumentNullException.ThrowIfNull(user);

        var jwtSettings = _configuration.GetSection("JwtSettings");

        string secretKey;
        try
        {
            secretKey = await _secretClient.GetSecretAsync("JwtSettings.SecretKey");
            if (string.IsNullOrEmpty(secretKey))
                secretKey = jwtSettings["SecretKey"] ?? string.Empty;
        }
        catch
        {
            throw new InvalidOperationException("Failed to retrieve JWT secret key");
        }

        if (string.IsNullOrEmpty(secretKey))
            throw new InvalidOperationException("JWT secret key not configured");

        var issuer = jwtSettings["Issuer"] ?? "Hackathon";
        var audience = jwtSettings["Audience"] ?? "Hackathon_API";

        if (!int.TryParse(jwtSettings["ExpirationMinutes"], out int expirationMinutes))
            expirationMinutes = 15;

        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, user.Id),
            new(JwtRegisteredClaimNames.Email, user.Email),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new("username", user.Username)
        };

        if (user.Roles != null)
        {
            foreach (var role in user.Roles)
                claims.Add(new Claim(ClaimTypes.Role, role));
        }

        var token = new JwtSecurityToken(
            issuer: issuer,
            audience: audience,
            claims: claims,
            expires: DateTime.UtcNow.AddMinutes(expirationMinutes),
            signingCredentials: creds
        );

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    public async Task<RefreshToken> GenerateRefreshTokenAsync(User user, string? deviceInfo = null)
    {
        ArgumentNullException.ThrowIfNull(user);

        var randomBytes = new byte[64];
        using (var rng = RandomNumberGenerator.Create())
        {
            rng.GetBytes(randomBytes);
        }

        var refreshToken = new RefreshToken
        {
            Token = Convert.ToBase64String(randomBytes),
            Expires = DateTime.UtcNow.AddDays(7),
            Created = DateTime.UtcNow,
            DeviceInfo = deviceInfo,
            IsRevoked = false
        };

        user.RefreshTokens ??= [];
        user.RefreshTokens.RemoveAll(t => t.IsExpired);
        user.RefreshTokens.Add(refreshToken);

        await _userRepository.UpdateAsync(user.Id, user);

        return refreshToken;
    }
}
