using System.Security.Cryptography;
using Hackathon.Application.Shared.Interfaces;
using Hackathon.Infrastructure.Services.SecretManagement;
using NSec.Cryptography;

namespace Hackathon.Infrastructure.Services.PasswordHashing;

public class Argon2IdPasswordHashingService : IPasswordHashingService
{
    private readonly PasswordBasedKeyDerivationAlgorithm _algorithm;
    private readonly ISecretClient _secretClient;
    private string? _pepper;

    public Argon2IdPasswordHashingService(ISecretClient secretClient)
    {
        _secretClient = secretClient ?? throw new ArgumentNullException(nameof(secretClient));

        var parameters = new Argon2Parameters
        {
            DegreeOfParallelism = 1,
            MemorySize = 65536,      // 64 MB
            NumberOfPasses = 3
        };

        _algorithm = PasswordBasedKeyDerivationAlgorithm.Argon2id(parameters);
    }

    private async Task<string> GetPepperAsync()
    {
        if (_pepper == null)
        {
            _pepper = await _secretClient.GetSecretAsync("Hashing.Pepper");
            if (string.IsNullOrEmpty(_pepper))
                throw new InvalidOperationException("Pepper is not configured in secrets.");
        }
        return _pepper;
    }

    private static string ApplyPepper(string password, string pepper) => password + pepper;

    public async Task<(string Hash, string Salt)> HashPasswordWithSaltAsync(string password)
    {
        if (string.IsNullOrEmpty(password))
            throw new ArgumentException("Password cannot be null or empty", nameof(password));

        string pepper = await GetPepperAsync();
        string pepperedPassword = ApplyPepper(password, pepper);

        byte[] salt = new byte[16];
        using (var rng = RandomNumberGenerator.Create())
        {
            rng.GetBytes(salt);
        }

        byte[] hash = _algorithm.DeriveBytes(pepperedPassword, salt, 64);
        return (Convert.ToBase64String(hash), Convert.ToBase64String(salt));
    }

    public async Task<bool> VerifyPasswordWithSaltAsync(string password, string hash, string salt)
    {
        if (string.IsNullOrEmpty(password))
            throw new ArgumentException("Password cannot be null or empty", nameof(password));
        if (string.IsNullOrEmpty(hash))
            throw new ArgumentException("Hash cannot be null or empty", nameof(hash));
        if (string.IsNullOrEmpty(salt))
            throw new ArgumentException("Salt cannot be null or empty", nameof(salt));

        try
        {
            string pepper = await GetPepperAsync();
            string pepperedPassword = ApplyPepper(password, pepper);

            byte[] storedHash = Convert.FromBase64String(hash);
            byte[] saltBytes = Convert.FromBase64String(salt);

            byte[] computedHash = _algorithm.DeriveBytes(pepperedPassword, saltBytes, storedHash.Length);
            return CryptographicOperations.FixedTimeEquals(computedHash, storedHash);
        }
        catch
        {
            return false;
        }
    }
}
