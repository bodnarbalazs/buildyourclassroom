using Hackathon.Application.Shared.Models;

namespace Hackathon.Application.Tests;

public class ResultTests
{
    [Fact]
    public void Success_CreatesSuccessResult()
    {
        var result = Result.Success();
        Assert.True(result.IsSuccess);
        Assert.False(result.IsFailure);
        Assert.Null(result.Error);
    }

    [Fact]
    public void Failure_CreatesFailureResult()
    {
        var result = Result.Failure("error");
        Assert.False(result.IsSuccess);
        Assert.True(result.IsFailure);
        Assert.Equal("error", result.Error);
    }

    [Fact]
    public void Success_WithValue_CreatesTypedResult()
    {
        var result = Result.Success(42);
        Assert.True(result.IsSuccess);
        Assert.Equal(42, result.Value);
        Assert.Null(result.Error);
    }

    [Fact]
    public void Failure_WithType_CreatesTypedFailureResult()
    {
        var result = Result.Failure<int>("error");
        Assert.False(result.IsSuccess);
        Assert.Equal("error", result.Error);
    }
}
