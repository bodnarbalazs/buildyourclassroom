namespace Hackathon.Api.Endpoints;

public static class AgendaEndpoints
{
    public static IEndpointRouteBuilder MapAgendaEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/agenda").WithTags("Lesson Agenda");

        group.MapPost("/generate", GenerateAgendaAsync);

        return routes;
    }

    internal static async Task<IResult> GenerateAgendaAsync(
        IHttpClientFactory httpClientFactory,
        HttpRequest request)
    {
        var client = httpClientFactory.CreateClient("microservice");
        var body = await new StreamContent(request.Body).ReadAsStringAsync();
        var response = await client.PostAsync("/api/v1/generate-agenda",
            new StringContent(body, System.Text.Encoding.UTF8, "application/json"));

        var content = await response.Content.ReadAsStringAsync();
        return Results.Content(content, "application/json", statusCode: (int)response.StatusCode);
    }
}
