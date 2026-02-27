namespace Hackathon.Infrastructure.Services.SecretManagement;

public interface ISecretClient
{
    Task<string> GetSecretAsync(string secretName);
    Task SetSecretAsync(string secretName, string secretValue);
}
