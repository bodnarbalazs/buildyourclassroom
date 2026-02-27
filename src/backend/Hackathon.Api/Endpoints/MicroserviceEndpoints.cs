using Hackathon.Domain.Messages;

namespace Hackathon.Api.Endpoints;

public static class MicroserviceEndpoints
{
    public static IEndpointRouteBuilder MapMicroserviceEndpoints(this IEndpointRouteBuilder routes)
    {
        routes.MapGroup("/api/micro").WithTags("Microservice").MapPost("/add", AddNumbersAsync);
        return routes;
    }

    internal static async Task<IResult> AddNumbersAsync(IAddNumbersClient client)
    {
        var response = await client.SendAsync(new AddNumbersCommand(1, 1));
        return Results.Ok(new { result = response.Sum });
    }
}
