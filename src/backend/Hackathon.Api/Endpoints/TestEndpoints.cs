namespace Hackathon.Api.Endpoints;

public static class TestEndpoints
{
    public static void MapTestEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapGet("/api/test", () => new { message = "Hello from Hackathon API" })
            .WithName("Test");
    }
}
