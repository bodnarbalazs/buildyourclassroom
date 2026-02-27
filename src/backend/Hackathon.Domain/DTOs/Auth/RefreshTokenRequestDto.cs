using Hackathon.Domain.Models.Common;

namespace Hackathon.Domain.DTOs.Auth;

[ConvertToTs]
public class RefreshTokenRequestDto
{
    public string UserId { get; set; } = string.Empty;
}
