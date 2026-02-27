using Hackathon.Domain.Models.Auth;

namespace Hackathon.Application.Auth.Commands.RefreshToken;

public class RefreshTokenResult
{
    public User User { get; set; } = null!;
    public string AccessToken { get; set; } = null!;
    public Domain.Models.Auth.RefreshToken RefreshToken { get; set; } = null!;
}
