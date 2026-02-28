using System.Net.Http.Headers;

namespace Hackathon.Api.Endpoints;

public static class AssessmentEndpoints
{
    public static IEndpointRouteBuilder MapAssessmentEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/assessment").WithTags("Lesson Assessment");

        group.MapPost("/generate", GenerateAssessmentsAsync).DisableAntiforgery();
        group.MapPost("/generate/from-transcript", GenerateFromTranscriptAsync);

        return routes;
    }

    internal static async Task<IResult> GenerateAssessmentsAsync(
        IHttpClientFactory httpClientFactory,
        HttpRequest request)
    {
        var client = httpClientFactory.CreateClient("microservice");

        var form = await request.ReadFormAsync();
        var file = form.Files.GetFile("file");
        if (file is null)
            return Results.BadRequest(new { detail = "No file provided." });

        using var content = new MultipartFormDataContent();

        var fileContent = new StreamContent(file.OpenReadStream());
        fileContent.Headers.ContentType = new MediaTypeHeaderValue(
            file.ContentType ?? "application/octet-stream");
        content.Add(fileContent, "file", file.FileName ?? "upload");

        if (form.TryGetValue("subject", out var subject))
            content.Add(new StringContent(subject!), "subject");
        if (form.TryGetValue("target_audience", out var audience))
            content.Add(new StringContent(audience!), "target_audience");
        if (form.TryGetValue("additional_instructions", out var instructions))
            content.Add(new StringContent(instructions!), "additional_instructions");

        var response = await client.PostAsync("/api/v1/generate-assessments", content);
        return await ForwardResponse(response);
    }

    internal static async Task<IResult> GenerateFromTranscriptAsync(
        IHttpClientFactory httpClientFactory,
        HttpRequest request)
    {
        var client = httpClientFactory.CreateClient("microservice");
        var body = await new StreamContent(request.Body).ReadAsStringAsync();
        var response = await client.PostAsync("/api/v1/generate-assessments/from-transcript",
            new StringContent(body, System.Text.Encoding.UTF8, "application/json"));
        return await ForwardResponse(response);
    }

    private static async Task<IResult> ForwardResponse(HttpResponseMessage response)
    {
        var content = await response.Content.ReadAsStringAsync();
        return Results.Content(content, "application/json", statusCode: (int)response.StatusCode);
    }
}
