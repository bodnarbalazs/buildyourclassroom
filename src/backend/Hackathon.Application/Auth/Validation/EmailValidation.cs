using System.Text.RegularExpressions;

namespace Hackathon.Application.Auth.Validation;

public static partial class EmailValidation
{
    [GeneratedRegex(@"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", RegexOptions.Compiled | RegexOptions.IgnoreCase)]
    private static partial Regex EmailRegex();

    public static bool IsValidEmail(string email)
    {
        return !string.IsNullOrWhiteSpace(email) && EmailRegex().IsMatch(email);
    }

    public static string? GetInvalidEmailReason(string email)
    {
        if (string.IsNullOrWhiteSpace(email))
            return "Email cannot be empty";

        if (!EmailRegex().IsMatch(email))
            return "Invalid email format";

        return null;
    }
}
