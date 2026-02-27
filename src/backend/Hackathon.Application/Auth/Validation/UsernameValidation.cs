using System.Text.RegularExpressions;

namespace Hackathon.Application.Auth.Validation;

public static partial class UsernameValidation
{
    [GeneratedRegex(@"^[\p{L}\p{M}\p{Nd}_-]{3,30}$", RegexOptions.Compiled)]
    private static partial Regex UsernameRegex();

    private static readonly HashSet<string> ReservedUsernames = new(StringComparer.OrdinalIgnoreCase)
    {
        "admin", "administrator", "system", "support", "root", "webmaster",
        "moderator", "mod", "superuser", "anonymous", "guest", "user",
        "login", "logout", "signup", "register", "account", "profile",
        "settings", "api", "master", "security", "token", "password"
    };

    public static bool IsValidUsername(string username)
    {
        return !string.IsNullOrWhiteSpace(username)
               && UsernameRegex().IsMatch(username)
               && !ReservedUsernames.Contains(username);
    }

    public static string? GetInvalidUsernameReason(string username)
    {
        if (string.IsNullOrWhiteSpace(username))
            return "Username cannot be empty";

        if (username.Length < 3)
            return "Username must be at least 3 characters long";

        if (username.Length > 30)
            return "Username cannot exceed 30 characters";

        if (!UsernameRegex().IsMatch(username))
            return "Username can only contain letters, numbers, underscores, and hyphens";

        if (ReservedUsernames.Contains(username))
            return "This username is reserved and cannot be used";

        return null;
    }
}
