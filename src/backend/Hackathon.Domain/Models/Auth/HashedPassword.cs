namespace Hackathon.Domain.Models.Auth;

public record HashedPassword
{
    public required string Hash { get; set; }
    public required string Salt { get; set; }
    public required int HashVersion { get; set; }
    public required int PepperVersion { get; set; }
}
