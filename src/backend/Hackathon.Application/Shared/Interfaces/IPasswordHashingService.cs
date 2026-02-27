namespace Hackathon.Application.Shared.Interfaces;

public interface IPasswordHashingService
{
    Task<(string Hash, string Salt)> HashPasswordWithSaltAsync(string password);
    Task<bool> VerifyPasswordWithSaltAsync(string password, string hash, string salt);
}
