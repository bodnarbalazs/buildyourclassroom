using System.Collections.Concurrent;
using System.Text.Json;
using System.Text.Json.Serialization;
using Hackathon.Domain.Messages;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;

namespace Hackathon.Infrastructure.Services.Messaging;

internal sealed class RabbitMqAddNumbersClient : IAddNumbersClient, IAsyncDisposable
{
    private readonly IChannel _channel;
    private readonly string _replyQueue;
    private readonly ConcurrentDictionary<string, TaskCompletionSource<AddNumbersResult>> _pending = new();
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    private RabbitMqAddNumbersClient(IChannel channel, string replyQueue)
    {
        _channel = channel;
        _replyQueue = replyQueue;
    }

    public static async Task<RabbitMqAddNumbersClient> CreateAsync(IConnection connection)
    {
        var channel = await connection.CreateChannelAsync();

        await channel.QueueDeclareAsync(
            queue: HackathonQueues.AddNumbers,
            durable: true,
            exclusive: false,
            autoDelete: false,
            arguments: null);

        var reply = await channel.QueueDeclareAsync(
            queue: "",
            durable: false,
            exclusive: true,
            autoDelete: true,
            arguments: null);

        var client = new RabbitMqAddNumbersClient(channel, reply.QueueName);

        var consumer = new AsyncEventingBasicConsumer(channel);
        consumer.ReceivedAsync += client.OnReplyReceivedAsync;
        await channel.BasicConsumeAsync(reply.QueueName, autoAck: true, consumer);

        return client;
    }

    private Task OnReplyReceivedAsync(object sender, BasicDeliverEventArgs args)
    {
        if (args.BasicProperties.CorrelationId is not { } corrId) return Task.CompletedTask;
        if (!_pending.TryRemove(corrId, out var tcs)) return Task.CompletedTask;

        try
        {
            var envelope = JsonSerializer.Deserialize<Envelope>(args.Body.Span, JsonOptions);
            tcs.TrySetResult(envelope!.Message);
        }
        catch (Exception ex)
        {
            tcs.TrySetException(ex);
        }

        return Task.CompletedTask;
    }

    public async Task<AddNumbersResult> SendAsync(AddNumbersCommand command, CancellationToken cancellationToken = default)
    {
        var corrId = Guid.NewGuid().ToString();
        var tcs = new TaskCompletionSource<AddNumbersResult>(TaskCreationOptions.RunContinuationsAsynchronously);
        _pending[corrId] = tcs;

        using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        cts.CancelAfter(TimeSpan.FromSeconds(30));

        await using var reg = cts.Token.Register(() =>
        {
            _pending.TryRemove(corrId, out _);
            tcs.TrySetCanceled(cts.Token);
        });

        var props = new BasicProperties { CorrelationId = corrId, ReplyTo = _replyQueue };
        var body = JsonSerializer.SerializeToUtf8Bytes(command, JsonOptions);

        await _channel.BasicPublishAsync(
            exchange: "",
            routingKey: HackathonQueues.AddNumbers,
            mandatory: false,
            basicProperties: props,
            body: body,
            cancellationToken: cts.Token);

        return await tcs.Task;
    }

    public async ValueTask DisposeAsync() => await _channel.DisposeAsync();

    private sealed record Envelope([property: JsonPropertyName("message")] AddNumbersResult Message);
}
