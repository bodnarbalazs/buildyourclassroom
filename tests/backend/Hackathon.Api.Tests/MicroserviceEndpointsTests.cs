using Hackathon.Api.Endpoints;
using Hackathon.Domain.Messages;
using MassTransit;
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
        var mockResponse = new Mock<Response<AddNumbersResult>>();
        mockResponse.Setup(r => r.Message).Returns(new AddNumbersResult(2));

        var mockClient = new Mock<IRequestClient<AddNumbersCommand>>();
        mockClient
            .Setup(c => c.GetResponse<AddNumbersResult>(
                It.IsAny<AddNumbersCommand>(),
                It.IsAny<CancellationToken>(),
                It.IsAny<RequestTimeout>()))
            .ReturnsAsync(mockResponse.Object);

        var result = await MicroserviceEndpoints.AddNumbersAsync(mockClient.Object);

        var statusResult = Assert.IsAssignableFrom<Microsoft.AspNetCore.Http.IStatusCodeHttpResult>(result);
        Assert.Equal(200, statusResult.StatusCode);
    }
}
