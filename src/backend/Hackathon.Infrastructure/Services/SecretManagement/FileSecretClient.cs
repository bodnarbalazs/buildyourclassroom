using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.Configuration;

namespace Hackathon.Infrastructure.Services.SecretManagement;

public class FileSecretClient : ISecretClient
{
    private readonly string _secretsFilePath;
    private readonly JsonNode _secretsCache;
    private readonly Lock _lock = new();

    public FileSecretClient(IConfiguration configuration)
    {
        var possiblePaths = new List<string>();

        var configPath = configuration["Secrets:FilePath"];
        if (!string.IsNullOrEmpty(configPath))
        {
            if (!Path.IsPathRooted(configPath))
            {
                var basePath = AppDomain.CurrentDomain.BaseDirectory;
                possiblePaths.Add(Path.Combine(basePath, configPath));
                var projectRoot = Path.GetFullPath(Path.Combine(basePath, "../../../.."));
                possiblePaths.Add(Path.Combine(projectRoot, configPath));
            }
            else
            {
                possiblePaths.Add(configPath);
            }
        }

        possiblePaths.Add(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "secrets.json"));
        possiblePaths.Add(@"C:\Users\User\Desktop\HackathonTemplate\secrets.json");
        possiblePaths.Add(Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "../../../../secrets.json")));

        _secretsFilePath = string.Empty;
        foreach (var path in possiblePaths)
        {
            Console.WriteLine($"Checking for secrets file at: {path}");
            if (File.Exists(path))
            {
                _secretsFilePath = path;
                Console.WriteLine($"Found secrets file at: {_secretsFilePath}");
                break;
            }
        }

        if (string.IsNullOrEmpty(_secretsFilePath))
        {
            _secretsFilePath = possiblePaths.FirstOrDefault() ?? "secrets.json";
            Console.WriteLine($"No secrets file found, defaulting to: {_secretsFilePath}");
        }

        var directory = Path.GetDirectoryName(_secretsFilePath);
        if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            Directory.CreateDirectory(directory);

        _secretsCache = LoadSecretsFromFile();
    }

    public Task<string> GetSecretAsync(string secretName)
    {
        try
        {
            if (secretName.Contains('.'))
            {
                var parts = secretName.Split('.');
                JsonNode current = _secretsCache;
                foreach (var part in parts)
                {
                    if (current == null) return Task.FromResult(string.Empty);
                    var next = current[part];
                    if (next == null) return Task.FromResult(string.Empty);
                    current = next;
                }
                return Task.FromResult(current?.ToString() ?? string.Empty);
            }
            else
            {
                var value = _secretsCache[secretName]?.ToString();
                return Task.FromResult(value ?? string.Empty);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error retrieving secret '{secretName}': {ex.Message}");
            return Task.FromResult(string.Empty);
        }
    }

    public Task SetSecretAsync(string secretName, string secretValue)
    {
        lock (_lock)
        {
            if (secretName.Contains('.'))
            {
                var parts = secretName.Split('.');
                JsonNode current = _secretsCache;
                for (int i = 0; i < parts.Length - 1; i++)
                {
                    var part = parts[i];
                    if (current[part] == null)
                        current[part] = new JsonObject();
                    current = current[part]!;
                }
                current[parts[^1]] = secretValue;
            }
            else
            {
                _secretsCache[secretName] = secretValue;
            }
            SaveSecretsToFile();
        }
        return Task.CompletedTask;
    }

    private JsonNode LoadSecretsFromFile()
    {
        lock (_lock)
        {
            if (File.Exists(_secretsFilePath))
            {
                try
                {
                    var json = File.ReadAllText(_secretsFilePath);
                    return JsonNode.Parse(json) ?? new JsonObject();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error loading secrets file: {ex.Message}");
                    return new JsonObject();
                }
            }
            return new JsonObject();
        }
    }

    private void SaveSecretsToFile()
    {
        lock (_lock)
        {
            var options = new JsonSerializerOptions { WriteIndented = true };
            var json = _secretsCache.ToJsonString(options);
            File.WriteAllText(_secretsFilePath, json);
        }
    }
}
