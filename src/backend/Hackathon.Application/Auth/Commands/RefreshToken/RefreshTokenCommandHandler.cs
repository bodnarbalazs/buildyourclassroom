using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Shared.Models;
using Hackathon.Application.Shared.Repositories;
using Microsoft.Extensions.Logging;

namespace Hackathon.Application.Auth.Commands.RefreshToken;

public partial class RefreshTokenCommandHandler
{
    private readonly IUserRepository _userRepository;
    private readonly IJwtService _jwtService;
    private readonly ILogger<RefreshTokenCommandHandler> _logger;

    public RefreshTokenCommandHandler(
        IUserRepository userRepository,
        IJwtService jwtService,
        ILogger<RefreshTokenCommandHandler> logger)
    {
        _userRepository = userRepository;
        _jwtService = jwtService;
        _logger = logger;
    }

    public async Task<Result<RefreshTokenResult>> HandleAsync(
        RefreshTokenCommand command,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(command.UserId))
            return Result.Failure<RefreshTokenResult>("User ID is required");
        if (string.IsNullOrWhiteSpace(command.Token))
            return Result.Failure<RefreshTokenResult>("Token is required");

        try
        {
            var user = await _userRepository.GetByIdAsync(command.UserId);
            if (user == null)
            {
                LogRefreshNonExistent(_logger, command.UserId);
                return Result.Failure<RefreshTokenResult>("Invalid refresh token");
            }

            var refreshToken = user.RefreshTokens?.Find(rt => rt.Token == command.Token);
            if (refreshToken == null || !refreshToken.IsActive)
            {
                LogRefreshInvalidToken(_logger, command.UserId);
                return Result.Failure<RefreshTokenResult>("Invalid refresh token");
            }

            refreshToken.IsRevoked = true;
            await _userRepository.UpdateAsync(user.Id, user);

            var accessToken = await _jwtService.GenerateJwtTokenAsync(user);
            var newRefreshToken = await _jwtService.GenerateRefreshTokenAsync(user);

            LogTokenRefreshed(_logger, user.Id);

            return Result.Success(new RefreshTokenResult
            {
                User = user,
                AccessToken = accessToken,
                RefreshToken = newRefreshToken
            });
        }
        catch (Exception ex)
        {
            LogRefreshError(_logger, ex, command.UserId);
            return Result.Failure<RefreshTokenResult>("An error occurred during token refresh.");
        }
    }

    [LoggerMessage(Level = LogLevel.Warning, Message = "Refresh attempt for non-existent user: {UserId}")]
    private static partial void LogRefreshNonExistent(ILogger logger, string userId);

    [LoggerMessage(Level = LogLevel.Warning, Message = "Refresh attempt with invalid token for user: {UserId}")]
    private static partial void LogRefreshInvalidToken(ILogger logger, string userId);

    [LoggerMessage(Level = LogLevel.Information, Message = "Token refreshed for user: {UserId}")]
    private static partial void LogTokenRefreshed(ILogger logger, string userId);

    [LoggerMessage(Level = LogLevel.Error, Message = "Error during token refresh for user: {UserId}")]
    private static partial void LogRefreshError(ILogger logger, Exception ex, string userId);
}
