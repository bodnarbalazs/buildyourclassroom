namespace Hackathon.Application.Auth.Commands.RegisterUser;

public class RegisterUserCommand
{
    public string Email { get; }
    public string Username { get; }
    public string Password { get; }

    public RegisterUserCommand(string email, string username, string password)
    {
        Email = email;
        Username = username;
        Password = password;
    }
}
