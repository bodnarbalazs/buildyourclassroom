using System.Net.Http.Headers;
using Microsoft.AspNetCore.Mvc;

namespace Hackathon.Api.Endpoints;

public static class SessionEndpoints
{
    public static IEndpointRouteBuilder MapSessionEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/emotion").WithTags("Emotion Sessions");

        group.MapPost("/sessions", CreateSessionAsync);
        group.MapGet("/sessions", ListSessionsAsync);
        group.MapGet("/sessions/{sessionId}", GetSessionAsync);
        group.MapPatch("/sessions/{sessionId}/end", EndSessionAsync);
        group.MapPost("/sessions/{sessionId}/snapshots", UploadSnapshotAsync).DisableAntiforgery();
        group.MapGet("/sessions/{sessionId}/summary", GetSessionSummaryAsync);
        group.MapGet("/sessions/{sessionId}/timeline", GetSessionTimelineAsync);

        return routes;
    }

    internal static async Task<IResult> CreateSessionAsync(
        IHttpClientFactory httpClientFactory,
        HttpRequest request)
    {
        var client = httpClientFactory.CreateClient("microservice");
        var body = await new StreamContent(request.Body).ReadAsStringAsync();
        var response = await client.PostAsync("/emotion/sessions",
            new StringContent(body, System.Text.Encoding.UTF8, "application/json"));
        return await ForwardResponse(response);
    }

    internal static async Task<IResult> ListSessionsAsync(
        IHttpClientFactory httpClientFactory,
        [FromQuery] int skip = 0,
        [FromQuery] int limit = 20)
    {
        var client = httpClientFactory.CreateClient("microservice");
        var response = await client.GetAsync($"/emotion/sessions?skip={skip}&limit={limit}");
        return await ForwardResponse(response);
    }

    internal static async Task<IResult> GetSessionAsync(
        IHttpClientFactory httpClientFactory,
        Guid sessionId)
    {
        var client = httpClientFactory.CreateClient("microservice");
        var response = await client.GetAsync($"/emotion/sessions/{sessionId}");
        return await ForwardResponse(response);
    }

    internal static async Task<IResult> EndSessionAsync(
        IHttpClientFactory httpClientFactory,
        Guid sessionId)
    {
        var client = httpClientFactory.CreateClient("microservice");
        var response = await client.PatchAsync($"/emotion/sessions/{sessionId}/end", null);
        return await ForwardResponse(response);
    }

    internal static async Task<IResult> UploadSnapshotAsync(
        IHttpClientFactory httpClientFactory,
        Guid sessionId,
        [FromForm] IFormFile file)
    {
        var client = httpClientFactory.CreateClient("microservice");

        using var stream = file.OpenReadStream();
        using var content = new MultipartFormDataContent();
        var fileContent = new StreamContent(stream);
        fileContent.Headers.ContentType = new MediaTypeHeaderValue(
            file.ContentType ?? "application/octet-stream");
        content.Add(fileContent, "file", file.FileName ?? "snapshot.jpg");

        var response = await client.PostAsync(
            $"/emotion/sessions/{sessionId}/snapshots", content);
        return await ForwardResponse(response);
    }

    internal static async Task<IResult> GetSessionSummaryAsync(
        IHttpClientFactory httpClientFactory,
        Guid sessionId)
    {
        var client = httpClientFactory.CreateClient("microservice");
        var response = await client.GetAsync($"/emotion/sessions/{sessionId}/summary");
        return await ForwardResponse(response);
    }

    internal static async Task<IResult> GetSessionTimelineAsync(
        IHttpClientFactory httpClientFactory,
        Guid sessionId,
        [FromQuery] int interval_seconds = 10)
    {
        var client = httpClientFactory.CreateClient("microservice");
        var response = await client.GetAsync(
            $"/emotion/sessions/{sessionId}/timeline?interval_seconds={interval_seconds}");
        return await ForwardResponse(response);
    }

    private static async Task<IResult> ForwardResponse(HttpResponseMessage response)
    {
        var content = await response.Content.ReadAsStringAsync();
        return Results.Content(content, "application/json", statusCode: (int)response.StatusCode);
    }
}
