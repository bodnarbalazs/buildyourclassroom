using Hackathon.Api.Endpoints;
using Hackathon.Domain.Messages;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Routing;
using Moq;

namespace Hackathon.Api.Tests;

public class MicroserviceEndpointsTests
{
    [Fact]
    public void MapMicroserviceEndpoints_RegistersRoutes()
    {
        var builder = WebApplication.CreateBuilder();
        var app = builder.Build();

        var result = app.MapMicroserviceEndpoints();

        Assert.Same(app, result);
    }

    [Fact]
    public async Task AddNumbersAsync_ReturnsOk()
    {
        var mockClient = new Mock<IAddNumbersClient>();
        mockClient
            .Setup(c => c.SendAsync(
                It.IsAny<AddNumbersCommand>(),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(new AddNumbersResult(2));

        var result = await MicroserviceEndpoints.AddNumbersAsync(mockClient.Object);

        var statusResult = Assert.IsAssignableFrom<Microsoft.AspNetCore.Http.IStatusCodeHttpResult>(result);
        Assert.Equal(200, statusResult.StatusCode);
    }
}
