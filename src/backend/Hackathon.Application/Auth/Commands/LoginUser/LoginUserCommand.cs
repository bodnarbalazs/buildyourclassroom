namespace Hackathon.Application.Auth.Commands.LoginUser;

public class LoginUserCommand
{
    public string EmailOrUsername { get; }
    public string Password { get; }

    public LoginUserCommand(string emailOrUsername, string password)
    {
        EmailOrUsername = emailOrUsername;
        Password = password;
    }
}
