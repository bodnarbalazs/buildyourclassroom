using Hackathon.Domain.Messages;
using Microsoft.AspNetCore.Mvc;

namespace Hackathon.Api.Endpoints;

public static class MicroserviceEndpoints
{
    public static IEndpointRouteBuilder MapMicroserviceEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/micro").WithTags("Microservice");
        group.MapPost("/add", AddNumbersAsync);
        group.MapPost("/analyze-snapshot", AnalyzeSnapshotAsync).DisableAntiforgery();
        return routes;
    }

    internal static async Task<IResult> AddNumbersAsync(IAddNumbersClient client)
    {
        var response = await client.SendAsync(new AddNumbersCommand(1, 1));
        return Results.Ok(new { result = response.Sum });
    }

    internal static async Task<IResult> AnalyzeSnapshotAsync(
        IAnalyzeSnapshotClient client,
        [FromForm] Guid sessionId,
        [FromForm] IFormFile file)
    {
        using var ms = new MemoryStream();
        await file.CopyToAsync(ms);
        var imageBase64 = Convert.ToBase64String(ms.ToArray());

        var response = await client.SendAsync(new AnalyzeSnapshotCommand(sessionId, imageBase64));
        return Results.Ok(response);
    }
}
