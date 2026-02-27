using Hackathon.Domain.Models.Auth;

namespace Hackathon.Domain.Tests;

public class HashedPasswordTests
{
    [Fact]
    public void HashedPassword_RecordEquality_Works()
    {
        var a = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 };
        var b = new HashedPassword { Hash = "h", Salt = "s", HashVersion = 1, PepperVersion = 1 };
        Assert.Equal(a, b);
    }

    [Fact]
    public void HashedPassword_RecordInequality_Works()
    {
        var a = new HashedPassword { Hash = "h1", Salt = "s", HashVersion = 1, PepperVersion = 1 };
        var b = new HashedPassword { Hash = "h2", Salt = "s", HashVersion = 1, PepperVersion = 1 };
        Assert.NotEqual(a, b);
    }
}
