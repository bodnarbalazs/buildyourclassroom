using Hackathon.Application.Shared.Repositories;
using Hackathon.Domain.Models.Auth;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Hackathon.Infrastructure.Database.Repositories;

public partial class PostgresUserRepository : EfRepository<User>, IUserRepository
{
    public PostgresUserRepository(
        AppDbContext context,
        ILogger<PostgresUserRepository> logger)
        : base(context, logger)
    {
    }

    public async Task<User?> GetByEmailAsync(string email)
    {
        try
        {
            var lowerEmail = email.ToLowerInvariant();
#pragma warning disable CA1304, CA1311, CA1862
            return await DbSet.FirstOrDefaultAsync(u => u.Email.ToLower() == lowerEmail);
#pragma warning restore CA1304, CA1311, CA1862
        }
        catch (Exception ex)
        {
            LogEmailError(Logger, ex, email);
            throw;
        }
    }

    public async Task<User?> GetByUsernameAsync(string username)
    {
        try
        {
            var lowerUsername = username.ToLowerInvariant();
#pragma warning disable CA1304, CA1311, CA1862
            return await DbSet.FirstOrDefaultAsync(u => u.Username.ToLower() == lowerUsername);
#pragma warning restore CA1304, CA1311, CA1862
        }
        catch (Exception ex)
        {
            LogUsernameError(Logger, ex, username);
            throw;
        }
    }

    public async Task<bool> EmailExistsAsync(string email)
    {
        try
        {
            var lowerEmail = email.ToLowerInvariant();
#pragma warning disable CA1304, CA1311, CA1862
            return await DbSet.AnyAsync(u => u.Email.ToLower() == lowerEmail);
#pragma warning restore CA1304, CA1311, CA1862
        }
        catch (Exception ex)
        {
            LogEmailExistsError(Logger, ex, email);
            throw;
        }
    }

    public async Task<bool> UsernameExistsAsync(string username)
    {
        try
        {
            var lowerUsername = username.ToLowerInvariant();
#pragma warning disable CA1304, CA1311, CA1862
            return await DbSet.AnyAsync(u => u.Username.ToLower() == lowerUsername);
#pragma warning restore CA1304, CA1311, CA1862
        }
        catch (Exception ex)
        {
            LogUsernameExistsError(Logger, ex, username);
            throw;
        }
    }

    [LoggerMessage(Level = LogLevel.Error, Message = "Error getting user by email {Email}")]
    private static partial void LogEmailError(ILogger logger, Exception ex, string email);

    [LoggerMessage(Level = LogLevel.Error, Message = "Error getting user by username {Username}")]
    private static partial void LogUsernameError(ILogger logger, Exception ex, string username);

    [LoggerMessage(Level = LogLevel.Error, Message = "Error checking email exists {Email}")]
    private static partial void LogEmailExistsError(ILogger logger, Exception ex, string email);

    [LoggerMessage(Level = LogLevel.Error, Message = "Error checking username exists {Username}")]
    private static partial void LogUsernameExistsError(ILogger logger, Exception ex, string username);
}
