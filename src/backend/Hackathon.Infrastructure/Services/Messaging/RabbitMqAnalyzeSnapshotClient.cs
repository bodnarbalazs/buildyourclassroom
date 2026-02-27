using System.Collections.Concurrent;
using System.Text.Json;
using System.Text.Json.Serialization;
using Hackathon.Domain.Messages;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;

namespace Hackathon.Infrastructure.Services.Messaging;

internal sealed class RabbitMqAnalyzeSnapshotClient : IAnalyzeSnapshotClient, IAsyncDisposable
{
    private readonly IChannel _channel;
    private readonly string _replyQueue;
    private readonly ConcurrentDictionary<string, TaskCompletionSource<AnalyzeSnapshotResult>> _pending = new();
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    private RabbitMqAnalyzeSnapshotClient(IChannel channel, string replyQueue)
    {
        _channel = channel;
        _replyQueue = replyQueue;
    }

    public static async Task<RabbitMqAnalyzeSnapshotClient> CreateAsync(IConnection connection)
    {
        var channel = await connection.CreateChannelAsync();

        await channel.QueueDeclareAsync(
            queue: HackathonQueues.AnalyzeSnapshot,
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

        var client = new RabbitMqAnalyzeSnapshotClient(channel, reply.QueueName);

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

    public async Task<AnalyzeSnapshotResult> SendAsync(AnalyzeSnapshotCommand command, CancellationToken cancellationToken = default)
    {
        var corrId = Guid.NewGuid().ToString();
        var tcs = new TaskCompletionSource<AnalyzeSnapshotResult>(TaskCreationOptions.RunContinuationsAsynchronously);
        _pending[corrId] = tcs;

        using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        cts.CancelAfter(TimeSpan.FromSeconds(60));

        await using var reg = cts.Token.Register(() =>
        {
            _pending.TryRemove(corrId, out _);
            tcs.TrySetCanceled(cts.Token);
        });

        var props = new BasicProperties { CorrelationId = corrId, ReplyTo = _replyQueue };
        var body = JsonSerializer.SerializeToUtf8Bytes(command, JsonOptions);

        await _channel.BasicPublishAsync(
            exchange: "",
            routingKey: HackathonQueues.AnalyzeSnapshot,
            mandatory: false,
            basicProperties: props,
            body: body,
            cancellationToken: cts.Token);

        return await tcs.Task;
    }

    public async ValueTask DisposeAsync() => await _channel.DisposeAsync();

    private sealed record Envelope([property: JsonPropertyName("message")] AnalyzeSnapshotResult Message);
}
