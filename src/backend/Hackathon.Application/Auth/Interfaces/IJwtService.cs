using Hackathon.Domain.Models.Auth;

namespace Hackathon.Application.Auth.Interfaces;

public interface IJwtService
{
    Task<string> GenerateJwtTokenAsync(User user);
    Task<RefreshToken> GenerateRefreshTokenAsync(User user, string? deviceInfo = null);
}
