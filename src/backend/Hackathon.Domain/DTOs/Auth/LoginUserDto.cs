using Hackathon.Domain.Models.Common;

namespace Hackathon.Domain.DTOs.Auth;

[ConvertToTs]
public class LoginUserDto
{
    public string EmailOrUsername { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}
