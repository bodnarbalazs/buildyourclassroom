namespace Hackathon.Domain.Messages;

public record AnalyzeSnapshotResult(
    Guid SnapshotId,
    Guid SessionId,
    DateTimeOffset CapturedAt,
    int FaceCount,
    double ProcessingMs,
    IReadOnlyList<FaceResultDto> Faces);
