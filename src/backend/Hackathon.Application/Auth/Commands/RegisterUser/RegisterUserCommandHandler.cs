using Hackathon.Application.Auth.Interfaces;
using Hackathon.Application.Auth.Validation;
using Hackathon.Application.Shared.Interfaces;
using Hackathon.Application.Shared.Models;
using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Models.Auth;
using Microsoft.Extensions.Logging;

namespace Hackathon.Application.Auth.Commands.RegisterUser;

public partial class RegisterUserCommandHandler
{
    private readonly IUserRepository _userRepository;
    private readonly IPasswordHashingService _passwordHashingService;
    private readonly IJwtService _jwtService;
    private readonly ILogger<RegisterUserCommandHandler> _logger;

    public RegisterUserCommandHandler(
        IUserRepository userRepository,
        IPasswordHashingService passwordHashingService,
        IJwtService jwtService,
        ILogger<RegisterUserCommandHandler> logger)
    {
        _userRepository = userRepository;
        _passwordHashingService = passwordHashingService;
        _jwtService = jwtService;
        _logger = logger;
    }

    public async Task<Result<RegisterUserResult>> HandleAsync(
        RegisterUserCommand command,
        CancellationToken cancellationToken = default)
    {
        var validationResult = ValidateCommand(command);
        if (validationResult.IsFailure)
            return Result.Failure<RegisterUserResult>(validationResult.Error!);

        try
        {
            var existingByEmail = await _userRepository.GetByEmailAsync(command.Email);
            if (existingByEmail != null)
                return Result.Failure<RegisterUserResult>($"Email '{command.Email}' is already registered");

            var existingByUsername = await _userRepository.GetByUsernameAsync(command.Username);
            if (existingByUsername != null)
                return Result.Failure<RegisterUserResult>($"Username '{command.Username}' is already taken");

            var (hash, salt) = await _passwordHashingService.HashPasswordWithSaltAsync(command.Password);

            var user = new User
            {
                Id = Guid.CreateVersion7().ToString(),
                Email = command.Email.ToLowerInvariant(),
                Username = command.Username,
                Password = new HashedPassword
                {
                    Hash = hash,
                    Salt = salt,
                    HashVersion = 1,
                    PepperVersion = 1
                },
                CreatedAt = DateTime.UtcNow,
                Roles = ["User"],
                RefreshTokens = []
            };

            await _userRepository.CreateAsync(user);

            var accessToken = await _jwtService.GenerateJwtTokenAsync(user);
            var refreshToken = await _jwtService.GenerateRefreshTokenAsync(user);

            LogUserRegistered(_logger, user.Id, user.Username);

            return Result.Success(new RegisterUserResult
            {
                User = user,
                AccessToken = accessToken,
                RefreshToken = refreshToken
            });
        }
        catch (Exception ex)
        {
            LogRegistrationError(_logger, ex, command.Email);
            return Result.Failure<RegisterUserResult>("An error occurred during registration.");
        }
    }

    private static Result ValidateCommand(RegisterUserCommand command)
    {
        if (string.IsNullOrWhiteSpace(command.Email))
            return Result.Failure("Email is required");
        if (string.IsNullOrWhiteSpace(command.Username))
            return Result.Failure("Username is required");
        if (string.IsNullOrWhiteSpace(command.Password))
            return Result.Failure("Password is required");

        var emailError = EmailValidation.GetInvalidEmailReason(command.Email);
        if (emailError != null) return Result.Failure(emailError);

        var usernameError = UsernameValidation.GetInvalidUsernameReason(command.Username);
        if (usernameError != null) return Result.Failure(usernameError);

        var passwordError = PasswordValidation.GetInvalidPasswordReason(command.Password);
        if (passwordError != null) return Result.Failure(passwordError);

        return Result.Success();
    }

    [LoggerMessage(Level = LogLevel.Information, Message = "User registered: {UserId}, Username: {Username}")]
    private static partial void LogUserRegistered(ILogger logger, string userId, string username);

    [LoggerMessage(Level = LogLevel.Error, Message = "Error during registration for email: {Email}")]
    private static partial void LogRegistrationError(ILogger logger, Exception ex, string email);
}
