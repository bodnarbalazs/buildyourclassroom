namespace Hackathon.Api.Endpoints;

public static class SimulationEndpoints
{
    public static IEndpointRouteBuilder MapSimulationEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/simulation").WithTags("Classroom Simulation");

        group.MapPost("/run", RunSimulationAsync);

        return routes;
    }

    internal static async Task<IResult> RunSimulationAsync(
        IHttpClientFactory httpClientFactory,
        HttpRequest request)
    {
        var client = httpClientFactory.CreateClient("microservice");
        var body = await new StreamContent(request.Body).ReadAsStringAsync();
        var response = await client.PostAsync("/api/v1/simulate",
            new StringContent(body, System.Text.Encoding.UTF8, "application/json"));

        var content = await response.Content.ReadAsStringAsync();
        return Results.Content(content, "application/json", statusCode: (int)response.StatusCode);
    }
}
