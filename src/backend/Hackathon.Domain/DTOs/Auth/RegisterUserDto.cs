using Hackathon.Domain.Models.Common;

namespace Hackathon.Domain.DTOs.Auth;

[ConvertToTs]
public class RegisterUserDto
{
    public string Email { get; set; } = string.Empty;
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}
