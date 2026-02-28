using Hackathon.Api.Hubs;

namespace Hackathon.Api.Tests.Hubs;

public class LiveFeedStateTests
{
    private readonly LiveFeedState _state = new();

    [Fact]
    public void TryAddCamera_FirstCamera_Succeeds()
    {
        var (success, cameraId) = _state.TryAddCamera("conn-1");

        Assert.True(success);
        Assert.Equal("cam-1", cameraId);
    }

    [Fact]
    public void TryAddCamera_FourCameras_AllSucceed()
    {
        var ids = new List<string?>();
        for (var i = 1; i <= 4; i++)
        {
            var (success, cameraId) = _state.TryAddCamera($"conn-{i}");
            Assert.True(success);
            ids.Add(cameraId);
        }

        Assert.Equal(["cam-1", "cam-2", "cam-3", "cam-4"], ids);
    }

    [Fact]
    public void TryAddCamera_FifthCamera_Rejected()
    {
        for (var i = 1; i <= 4; i++)
            _state.TryAddCamera($"conn-{i}");

        var (success, cameraId) = _state.TryAddCamera("conn-5");

        Assert.False(success);
        Assert.Null(cameraId);
    }

    [Fact]
    public void TryAddCamera_FillsGaps()
    {
        _state.TryAddCamera("conn-1"); // cam-1
        _state.TryAddCamera("conn-2"); // cam-2
        _state.TryAddCamera("conn-3"); // cam-3

        _state.RemoveByConnectionId("conn-2"); // free cam-2

        var (success, cameraId) = _state.TryAddCamera("conn-4");

        Assert.True(success);
        Assert.Equal("cam-2", cameraId);
    }

    [Fact]
    public void RemoveByConnectionId_ExistingCamera_ReturnsId()
    {
        _state.TryAddCamera("conn-1");

        var removed = _state.RemoveByConnectionId("conn-1");

        Assert.Equal("cam-1", removed);
    }

    [Fact]
    public void RemoveByConnectionId_UnknownConnection_ReturnsNull()
    {
        var removed = _state.RemoveByConnectionId("unknown");

        Assert.Null(removed);
    }

    [Fact]
    public void RemoveCamera_FreesSlot()
    {
        for (var i = 1; i <= 4; i++)
            _state.TryAddCamera($"conn-{i}");

        Assert.Equal(4, _state.ActiveCameraCount);

        _state.RemoveByConnectionId("conn-3");

        Assert.Equal(3, _state.ActiveCameraCount);

        var (success, _) = _state.TryAddCamera("conn-5");
        Assert.True(success);
    }

    [Fact]
    public void TrySetDisplay_ReplacePrevious()
    {
        _state.TrySetDisplay("display-1");
        Assert.Equal("display-1", _state.DisplayConnectionId);

        _state.TrySetDisplay("display-2");
        Assert.Equal("display-2", _state.DisplayConnectionId);
    }

    [Fact]
    public void Clear_ResetsEverything()
    {
        _state.TrySetDisplay("display-1");
        _state.TryAddCamera("conn-1");

        _state.Clear();

        Assert.Null(_state.DisplayConnectionId);
        Assert.Equal(0, _state.ActiveCameraCount);
    }

    [Fact]
    public void ActiveCameraCount_Accurate()
    {
        Assert.Equal(0, _state.ActiveCameraCount);

        _state.TryAddCamera("conn-1");
        Assert.Equal(1, _state.ActiveCameraCount);

        _state.TryAddCamera("conn-2");
        Assert.Equal(2, _state.ActiveCameraCount);

        _state.RemoveByConnectionId("conn-1");
        Assert.Equal(1, _state.ActiveCameraCount);
    }

    [Fact]
    public void IsDisplay_ReturnsTrueForDisplay()
    {
        _state.TrySetDisplay("display-1");

        Assert.True(_state.IsDisplay("display-1"));
        Assert.False(_state.IsDisplay("other"));
    }

    [Fact]
    public void GetCameraConnectionId_ReturnsCorrectId()
    {
        _state.TryAddCamera("conn-1");

        Assert.Equal("conn-1", _state.GetCameraConnectionId("cam-1"));
        Assert.Null(_state.GetCameraConnectionId("cam-2"));
    }
}
