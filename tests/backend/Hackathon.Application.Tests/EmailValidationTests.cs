using Hackathon.Application.Auth.Validation;

namespace Hackathon.Application.Tests;

public class EmailValidationTests
{
    [Theory]
    [InlineData("user@example.com", true)]
    [InlineData("test.user@domain.co", true)]
    [InlineData("a@b.cd", true)]
    public void IsValidEmail_ValidEmails_ReturnsTrue(string email, bool expected)
    {
        Assert.Equal(expected, EmailValidation.IsValidEmail(email));
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    public void IsValidEmail_EmptyOrWhitespace_ReturnsFalse(string email)
    {
        Assert.False(EmailValidation.IsValidEmail(email));
    }

    [Theory]
    [InlineData("notanemail")]
    [InlineData("@domain.com")]
    [InlineData("user@")]
    [InlineData("user@.com")]
    public void IsValidEmail_InvalidFormat_ReturnsFalse(string email)
    {
        Assert.False(EmailValidation.IsValidEmail(email));
    }

    [Fact]
    public void GetInvalidEmailReason_Empty_ReturnsEmptyMessage()
    {
        Assert.Equal("Email cannot be empty", EmailValidation.GetInvalidEmailReason(""));
    }

    [Fact]
    public void GetInvalidEmailReason_Whitespace_ReturnsEmptyMessage()
    {
        Assert.Equal("Email cannot be empty", EmailValidation.GetInvalidEmailReason("   "));
    }

    [Fact]
    public void GetInvalidEmailReason_InvalidFormat_ReturnsFormatMessage()
    {
        Assert.Equal("Invalid email format", EmailValidation.GetInvalidEmailReason("notanemail"));
    }

    [Fact]
    public void GetInvalidEmailReason_ValidEmail_ReturnsNull()
    {
        Assert.Null(EmailValidation.GetInvalidEmailReason("user@example.com"));
    }
}
