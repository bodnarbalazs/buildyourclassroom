using System.Text.Json.Serialization;

namespace Hackathon.Domain.Models.Auth;

public class RefreshToken
{
    public string Token { get; set; } = string.Empty;
    public DateTime Expires { get; set; }
    public DateTime Created { get; set; } = DateTime.UtcNow;
    public string? DeviceInfo { get; set; }
    public bool IsRevoked { get; set; }

    [JsonIgnore]
    public bool IsExpired => DateTime.UtcNow >= Expires;

    [JsonIgnore]
    public bool IsActive => !IsRevoked && !IsExpired;
}
