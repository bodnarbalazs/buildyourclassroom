using Hackathon.Application.Shared.Models;
using Hackathon.Application.Shared.Repositories;
using Microsoft.Extensions.Logging;

namespace Hackathon.Application.Auth.Commands.Logout;

public partial class LogoutCommandHandler
{
    private readonly IUserRepository _userRepository;
    private readonly ILogger<LogoutCommandHandler> _logger;

    public LogoutCommandHandler(
        IUserRepository userRepository,
        ILogger<LogoutCommandHandler> logger)
    {
        _userRepository = userRepository;
        _logger = logger;
    }

    public async Task<Result> HandleAsync(
        LogoutCommand command,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(command.UserId))
            return Result.Failure("User ID is required");
        if (string.IsNullOrWhiteSpace(command.Token))
            return Result.Failure("Token is required");

        try
        {
            var user = await _userRepository.GetByIdAsync(command.UserId);
            if (user == null)
            {
                LogLogoutNonExistent(_logger, command.UserId);
                return Result.Failure("User not found");
            }

            var refreshToken = user.RefreshTokens?.Find(rt => rt.Token == command.Token);
            if (refreshToken == null)
            {
                LogLogoutNoToken(_logger, command.UserId);
                return Result.Failure("Refresh token not found");
            }

            refreshToken.IsRevoked = true;
            await _userRepository.UpdateAsync(user.Id, user);

            LogUserLoggedOut(_logger, user.Id);
            return Result.Success();
        }
        catch (Exception ex)
        {
            LogLogoutError(_logger, ex, command.UserId);
            return Result.Failure("An error occurred during logout.");
        }
    }

    [LoggerMessage(Level = LogLevel.Warning, Message = "Logout attempt for non-existent user: {UserId}")]
    private static partial void LogLogoutNonExistent(ILogger logger, string userId);

    [LoggerMessage(Level = LogLevel.Warning, Message = "Logout attempt with non-existent token for user: {UserId}")]
    private static partial void LogLogoutNoToken(ILogger logger, string userId);

    [LoggerMessage(Level = LogLevel.Information, Message = "User logged out: {UserId}")]
    private static partial void LogUserLoggedOut(ILogger logger, string userId);

    [LoggerMessage(Level = LogLevel.Error, Message = "Error during logout for user: {UserId}")]
    private static partial void LogLogoutError(ILogger logger, Exception ex, string userId);
}
