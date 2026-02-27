namespace Hackathon.Domain.Messages;

public interface IAnalyzeSnapshotClient
{
    Task<AnalyzeSnapshotResult> SendAsync(AnalyzeSnapshotCommand command, CancellationToken cancellationToken = default);
}
