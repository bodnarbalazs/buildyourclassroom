using Hackathon.Domain.Models.Auth;

namespace Hackathon.Domain.Tests;

public class RefreshTokenTests
{
    [Fact]
    public void IsExpired_WhenExpiresInFuture_ReturnsFalse()
    {
        var token = new RefreshToken { Expires = DateTime.UtcNow.AddDays(1) };
        Assert.False(token.IsExpired);
    }

    [Fact]
    public void IsExpired_WhenExpiresInPast_ReturnsTrue()
    {
        var token = new RefreshToken { Expires = DateTime.UtcNow.AddDays(-1) };
        Assert.True(token.IsExpired);
    }

    [Fact]
    public void IsActive_WhenNotRevokedAndNotExpired_ReturnsTrue()
    {
        var token = new RefreshToken
        {
            Expires = DateTime.UtcNow.AddDays(1),
            IsRevoked = false
        };
        Assert.True(token.IsActive);
    }

    [Fact]
    public void IsActive_WhenRevoked_ReturnsFalse()
    {
        var token = new RefreshToken
        {
            Expires = DateTime.UtcNow.AddDays(1),
            IsRevoked = true
        };
        Assert.False(token.IsActive);
    }

    [Fact]
    public void IsActive_WhenExpired_ReturnsFalse()
    {
        var token = new RefreshToken
        {
            Expires = DateTime.UtcNow.AddDays(-1),
            IsRevoked = false
        };
        Assert.False(token.IsActive);
    }

    [Fact]
    public void IsActive_WhenRevokedAndExpired_ReturnsFalse()
    {
        var token = new RefreshToken
        {
            Expires = DateTime.UtcNow.AddDays(-1),
            IsRevoked = true
        };
        Assert.False(token.IsActive);
    }

    [Fact]
    public void DefaultValues_AreCorrect()
    {
        var token = new RefreshToken();
        Assert.Equal(string.Empty, token.Token);
        Assert.False(token.IsRevoked);
        Assert.Null(token.DeviceInfo);
    }
}
