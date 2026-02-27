using Hackathon.Domain.Models.Common;

namespace Hackathon.Domain.DTOs.Auth;

[ConvertToTs]
public class AuthResponseDto
{
    public DateTime ExpiresAt { get; set; }
    public UserDto User { get; set; } = null!;
}
