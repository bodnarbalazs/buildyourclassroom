namespace Hackathon.Domain.Messages;

public interface IAddNumbersClient
{
    Task<AddNumbersResult> SendAsync(AddNumbersCommand command, CancellationToken cancellationToken = default);
}
