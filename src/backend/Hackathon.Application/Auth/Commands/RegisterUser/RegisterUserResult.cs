namespace Hackathon.Application.Auth.Commands.RegisterUser;

public class RegisterUserResult
{
    public Domain.Models.Auth.User User { get; set; } = null!;
    public string AccessToken { get; set; } = null!;
    public Domain.Models.Auth.RefreshToken RefreshToken { get; set; } = null!;
}
