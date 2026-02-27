using System.Text.RegularExpressions;

namespace Hackathon.Application.Auth.Validation;

public static partial class PasswordValidation
{
    private const int MinLength = 12;
    private const int MaxLength = 128;

    [GeneratedRegex("[A-Z]", RegexOptions.Compiled)]
    private static partial Regex HasUpperCase();

    [GeneratedRegex("[a-z]", RegexOptions.Compiled)]
    private static partial Regex HasLowerCase();

    [GeneratedRegex("[0-9]", RegexOptions.Compiled)]
    private static partial Regex HasDigit();

    [GeneratedRegex("[^a-zA-Z0-9]", RegexOptions.Compiled)]
    private static partial Regex HasSpecialChar();

    public static bool IsValidPassword(string password)
    {
        if (string.IsNullOrEmpty(password))
            return false;

        if (password.Length < MinLength || password.Length > MaxLength)
            return false;

        int complexityScore = 0;
        if (HasUpperCase().IsMatch(password)) complexityScore++;
        if (HasLowerCase().IsMatch(password)) complexityScore++;
        if (HasDigit().IsMatch(password)) complexityScore++;
        if (HasSpecialChar().IsMatch(password)) complexityScore++;

        return complexityScore >= 3;
    }

    public static string? GetInvalidPasswordReason(string password)
    {
        if (string.IsNullOrEmpty(password))
            return "Password cannot be empty";

        if (password.Length < MinLength)
            return $"Password must be at least {MinLength} characters long";

        if (password.Length > MaxLength)
            return $"Password cannot exceed {MaxLength} characters";

        int complexityScore = 0;
        if (HasUpperCase().IsMatch(password)) complexityScore++;
        if (HasLowerCase().IsMatch(password)) complexityScore++;
        if (HasDigit().IsMatch(password)) complexityScore++;
        if (HasSpecialChar().IsMatch(password)) complexityScore++;

        if (complexityScore < 3)
            return "Password must contain at least 3 of the following: uppercase letters, lowercase letters, numbers, and special characters";

        return null;
    }
}
