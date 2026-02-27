namespace Hackathon.Application.Auth.Commands.Logout;

public class LogoutCommand
{
    public string UserId { get; }
    public string Token { get; }

    public LogoutCommand(string userId, string token)
    {
        UserId = userId;
        Token = token;
    }
}
