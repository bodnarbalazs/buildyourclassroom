using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Shared.Interfaces;
using Hackathon.Application.Shared.Models;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Models.Auth;
using Microsoft.Extensions.Logging;

namespace Hackathon.Application.Auth.Commands.LoginUser;

public partial class LoginUserCommandHandler
{
    private readonly IUserRepository _userRepository;
    private readonly IPasswordHashingService _passwordHashingService;
    private readonly IJwtService _jwtService;
    private readonly ILogger<LoginUserCommandHandler> _logger;

    public LoginUserCommandHandler(
        IUserRepository userRepository,
        IPasswordHashingService passwordHashingService,
        IJwtService jwtService,
        ILogger<LoginUserCommandHandler> logger)
    {
        _userRepository = userRepository;
        _passwordHashingService = passwordHashingService;
        _jwtService = jwtService;
        _logger = logger;
    }

    public async Task<Result<LoginUserResult>> HandleAsync(
        LoginUserCommand command,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(command.EmailOrUsername))
            return Result.Failure<LoginUserResult>("Email or username is required");
        if (string.IsNullOrWhiteSpace(command.Password))
            return Result.Failure<LoginUserResult>("Password is required");

        try
        {
            User? user;
            if (command.EmailOrUsername.Contains('@'))
                user = await _userRepository.GetByEmailAsync(command.EmailOrUsername.ToLowerInvariant());
            else
                user = await _userRepository.GetByUsernameAsync(command.EmailOrUsername);

            if (user == null)
            {
                LogLoginNonExistent(_logger, command.EmailOrUsername);
                return Result.Failure<LoginUserResult>("Invalid credentials");
            }

            bool isPasswordValid = await _passwordHashingService.VerifyPasswordWithSaltAsync(
                command.Password,
                user.Password.Hash,
                user.Password.Salt);

            if (!isPasswordValid)
                return Result.Failure<LoginUserResult>("Invalid credentials");

            user.LastLoginAt = DateTime.UtcNow;
            await _userRepository.UpdateAsync(user.Id, user);

            var accessToken = await _jwtService.GenerateJwtTokenAsync(user);
            var refreshToken = await _jwtService.GenerateRefreshTokenAsync(user);

            LogUserLoggedIn(_logger, user.Id);

            return Result.Success(new LoginUserResult
            {
                User = user,
                AccessToken = accessToken,
                RefreshToken = refreshToken
            });
        }
        catch (Exception ex)
        {
            LogLoginError(_logger, ex, command.EmailOrUsername);
            return Result.Failure<LoginUserResult>("An error occurred during login.");
        }
    }

    [LoggerMessage(Level = LogLevel.Warning, Message = "Login attempt for non-existent user: {EmailOrUsername}")]
    private static partial void LogLoginNonExistent(ILogger logger, string emailOrUsername);

    [LoggerMessage(Level = LogLevel.Information, Message = "User logged in: {UserId}")]
    private static partial void LogUserLoggedIn(ILogger logger, string userId);

    [LoggerMessage(Level = LogLevel.Error, Message = "Error during login for: {EmailOrUsername}")]
    private static partial void LogLoginError(ILogger logger, Exception ex, string emailOrUsername);
}
