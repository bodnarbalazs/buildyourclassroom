namespace Hackathon.Domain.Models.Auth;

public class User
{
    public required string Id { get; set; }
    public required string Email { get; set; }
    public required string Username { get; set; }
    public required HashedPassword Password { get; set; }
    public List<RefreshToken> RefreshTokens { get; set; } = [];
    public List<string> Roles { get; set; } = [];
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? LastLoginAt { get; set; }
}
