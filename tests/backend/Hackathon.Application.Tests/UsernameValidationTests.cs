using Hackathon.Application.Auth.Validation;

namespace Hackathon.Application.Tests;

public class UsernameValidationTests
{
    [Theory]
    [InlineData("validuser", true)]
    [InlineData("user_name", true)]
    [InlineData("user-name", true)]
    [InlineData("abc", true)]
    public void IsValidUsername_ValidUsernames_ReturnsTrue(string username, bool expected)
    {
        Assert.Equal(expected, UsernameValidation.IsValidUsername(username));
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    public void IsValidUsername_EmptyOrWhitespace_ReturnsFalse(string username)
    {
        Assert.False(UsernameValidation.IsValidUsername(username));
    }

    [Theory]
    [InlineData("ab")]
    public void IsValidUsername_TooShort_ReturnsFalse(string username)
    {
        Assert.False(UsernameValidation.IsValidUsername(username));
    }

    [Fact]
    public void IsValidUsername_TooLong_ReturnsFalse()
    {
        Assert.False(UsernameValidation.IsValidUsername(new string('a', 31)));
    }

    [Theory]
    [InlineData("admin")]
    [InlineData("Admin")]
    [InlineData("root")]
    [InlineData("system")]
    [InlineData("password")]
    public void IsValidUsername_Reserved_ReturnsFalse(string username)
    {
        Assert.False(UsernameValidation.IsValidUsername(username));
    }

    [Theory]
    [InlineData("user name")]
    [InlineData("user@name")]
    [InlineData("user.name")]
    public void IsValidUsername_InvalidChars_ReturnsFalse(string username)
    {
        Assert.False(UsernameValidation.IsValidUsername(username));
    }

    [Fact]
    public void GetInvalidUsernameReason_Empty_ReturnsEmpty()
    {
        Assert.Equal("Username cannot be empty", UsernameValidation.GetInvalidUsernameReason(""));
    }

    [Fact]
    public void GetInvalidUsernameReason_TooShort_ReturnsTooShort()
    {
        Assert.Equal("Username must be at least 3 characters long",
            UsernameValidation.GetInvalidUsernameReason("ab"));
    }

    [Fact]
    public void GetInvalidUsernameReason_TooLong_ReturnsTooLong()
    {
        Assert.Equal("Username cannot exceed 30 characters",
            UsernameValidation.GetInvalidUsernameReason(new string('a', 31)));
    }

    [Fact]
    public void GetInvalidUsernameReason_InvalidChars_ReturnsInvalidChars()
    {
        Assert.Equal("Username can only contain letters, numbers, underscores, and hyphens",
            UsernameValidation.GetInvalidUsernameReason("user@name"));
    }

    [Fact]
    public void GetInvalidUsernameReason_Reserved_ReturnsReserved()
    {
        Assert.Equal("This username is reserved and cannot be used",
            UsernameValidation.GetInvalidUsernameReason("admin"));
    }

    [Fact]
    public void GetInvalidUsernameReason_Valid_ReturnsNull()
    {
        Assert.Null(UsernameValidation.GetInvalidUsernameReason("validuser"));
    }
}
