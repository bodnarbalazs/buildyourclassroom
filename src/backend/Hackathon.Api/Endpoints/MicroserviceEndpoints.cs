using Hackathon.Domain.Messages;
using MassTransit;

namespace Hackathon.Api.Endpoints;

public static class MicroserviceEndpoints
{
    public static IEndpointRouteBuilder MapMicroserviceEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/micro").WithTags("Microservice");

        group.MapPost("/add", AddNumbersAsync);

        return routes;
    }

    internal static async Task<IResult> AddNumbersAsync(
        IRequestClient<AddNumbersCommand> client)
    {
        var response = await client.GetResponse<AddNumbersResult>(
            new AddNumbersCommand(1, 1));

        return Results.Ok(new { result = response.Message.Sum });
    }
}
