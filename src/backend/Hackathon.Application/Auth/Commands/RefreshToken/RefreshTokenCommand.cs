namespace Hackathon.Application.Auth.Commands.RefreshToken;

public class RefreshTokenCommand
{
    public string UserId { get; }
    public string Token { get; }

    public RefreshTokenCommand(string userId, string token)
    {
        UserId = userId;
        Token = token;
    }
}
