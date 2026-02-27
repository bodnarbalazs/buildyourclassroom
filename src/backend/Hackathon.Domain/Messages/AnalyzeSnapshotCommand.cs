namespace Hackathon.Domain.Messages;

public record AnalyzeSnapshotCommand(Guid SessionId, string ImageBase64);
