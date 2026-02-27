using Hackathon.Domain.Models.Auth;

namespace Hackathon.Domain.Tests;

public class UserTests
{
    [Fact]
    public void User_CanBeCreated_WithRequiredProperties()
    {
        var user = new User
        {
            Id = "test-id",
            Email = "test@example.com",
            Username = "testuser",
            Password = new HashedPassword
            {
                Hash = "hash",
                Salt = "salt",
                HashVersion = 1,
                PepperVersion = 1
            }
        };

        Assert.Equal("test-id", user.Id);
        Assert.Equal("test@example.com", user.Email);
        Assert.Equal("testuser", user.Username);
        Assert.Empty(user.RefreshTokens);
        Assert.Empty(user.Roles);
        Assert.Null(user.LastLoginAt);
    }
}
