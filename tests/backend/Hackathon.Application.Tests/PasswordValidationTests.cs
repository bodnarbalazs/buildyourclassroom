using Hackathon.Application.Auth.Validation;

namespace Hackathon.Application.Tests;

public class PasswordValidationTests
{
    [Fact]
    public void IsValidPassword_Empty_ReturnsFalse()
    {
        Assert.False(PasswordValidation.IsValidPassword(""));
    }

    [Fact]
    public void IsValidPassword_TooShort_ReturnsFalse()
    {
        Assert.False(PasswordValidation.IsValidPassword("Abc123!"));
    }

    [Fact]
    public void IsValidPassword_TooLong_ReturnsFalse()
    {
        Assert.False(PasswordValidation.IsValidPassword(new string('A', 129) + "a1!"));
    }

    [Theory]
    [InlineData("Abcdefgh123!")] // upper + lower + digit + special = 4
    [InlineData("Abcdefghijk1")] // upper + lower + digit = 3
    [InlineData("Abcdefghijk!")] // upper + lower + special = 3
    [InlineData("abcdefgh123!")] // lower + digit + special = 3
    [InlineData("ABCDEFGH123!")] // upper + digit + special = 3
    public void IsValidPassword_MeetsComplexity_ReturnsTrue(string password)
    {
        Assert.True(PasswordValidation.IsValidPassword(password));
    }

    [Theory]
    [InlineData("abcdefghijkl")] // only lower = 1
    [InlineData("ABCDEFGHIJKL")] // only upper = 1
    [InlineData("123456789012")] // only digits = 1
    [InlineData("!!!!!!!!!!!!")]  // only special = 1
    [InlineData("abcdefABCDEF")] // upper + lower = 2
    [InlineData("123456789!@#")] // digit + special = 2
    public void IsValidPassword_InsufficientComplexity_ReturnsFalse(string password)
    {
        Assert.False(PasswordValidation.IsValidPassword(password));
    }

    [Fact]
    public void GetInvalidPasswordReason_Empty_ReturnsEmpty()
    {
        Assert.Equal("Password cannot be empty", PasswordValidation.GetInvalidPasswordReason(""));
    }

    [Fact]
    public void GetInvalidPasswordReason_TooShort_ReturnsTooShort()
    {
        Assert.Contains("at least 12", PasswordValidation.GetInvalidPasswordReason("short"));
    }

    [Fact]
    public void GetInvalidPasswordReason_TooLong_ReturnsTooLong()
    {
        Assert.Contains("cannot exceed 128", PasswordValidation.GetInvalidPasswordReason(new string('A', 129)));
    }

    [Fact]
    public void GetInvalidPasswordReason_LowComplexity_ReturnsComplexityMsg()
    {
        Assert.Contains("must contain at least 3",
            PasswordValidation.GetInvalidPasswordReason("abcdefghijkl"));
    }

    [Fact]
    public void GetInvalidPasswordReason_Valid_ReturnsNull()
    {
        Assert.Null(PasswordValidation.GetInvalidPasswordReason("Abcdefgh123!"));
    }
}
