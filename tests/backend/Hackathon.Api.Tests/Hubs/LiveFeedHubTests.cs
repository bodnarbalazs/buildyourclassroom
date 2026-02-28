using Hackathon.Api.Hubs;
using Microsoft.AspNetCore.SignalR;
using Moq;

namespace Hackathon.Api.Tests.Hubs;

public class LiveFeedHubTests : IDisposable
{
    private readonly LiveFeedState _state = new();
    private readonly Mock<IHubCallerClients> _clients = new();
    private readonly Mock<HubCallerContext> _context = new();
    private readonly Mock<ISingleClientProxy> _callerProxy = new();
    private readonly LiveFeedHub _hub;

    public LiveFeedHubTests()
    {
        _clients.Setup(c => c.Caller).Returns(_callerProxy.Object);
        _hub = new LiveFeedHub(_state)
        {
            Clients = _clients.Object,
            Context = _context.Object
        };
    }

    public void Dispose() => _hub.Dispose();

    private void SetConnectionId(string id) =>
        _context.Setup(c => c.ConnectionId).Returns(id);

    private Mock<ISingleClientProxy> SetupClientProxy(string connectionId)
    {
        var proxy = new Mock<ISingleClientProxy>();
        _clients.Setup(c => c.Client(connectionId)).Returns(proxy.Object);
        return proxy;
    }

    [Fact]
    public async Task JoinAsDisplay_RegistersDisplay()
    {
        SetConnectionId("display-1");

        await _hub.JoinAsDisplay();

        Assert.Equal("display-1", _state.DisplayConnectionId);
    }

    [Fact]
    public async Task JoinAsCamera_WhenDisplayActive_SendsCameraJoined()
    {
        _state.TrySetDisplay("display-1");
        var displayProxy = SetupClientProxy("display-1");
        SetConnectionId("camera-conn-1");

        await _hub.JoinAsCamera();

        displayProxy.Verify(p => p.SendCoreAsync(
            "CameraJoined",
            It.Is<object?[]>(args => args.Length == 1 && (string)args[0]! == "cam-1"),
            default));
    }

    [Fact]
    public async Task JoinAsCamera_WhenFull_SendsRejection()
    {
        _state.TrySetDisplay("display-1");
        SetupClientProxy("display-1");

        for (var i = 1; i <= 4; i++)
            _state.TryAddCamera($"cam-conn-{i}");

        SetConnectionId("cam-conn-5");

        await _hub.JoinAsCamera();

        _callerProxy.Verify(p => p.SendCoreAsync(
            "CameraRejected",
            It.Is<object?[]>(args => ((string)args[0]!).Contains("4/4")),
            default));
    }

    [Fact]
    public async Task JoinAsCamera_WhenNoDisplay_SendsNoSession()
    {
        SetConnectionId("camera-conn-1");

        await _hub.JoinAsCamera();

        _callerProxy.Verify(p => p.SendCoreAsync(
            "CameraRejected",
            It.Is<object?[]>(args => (string)args[0]! == "No active session"),
            default));
    }

    [Fact]
    public async Task OnDisconnected_Camera_NotifiesDisplay()
    {
        _state.TrySetDisplay("display-1");
        var displayProxy = SetupClientProxy("display-1");
        _state.TryAddCamera("camera-conn-1");
        SetConnectionId("camera-conn-1");

        await _hub.OnDisconnectedAsync(null);

        displayProxy.Verify(p => p.SendCoreAsync(
            "CameraLeft",
            It.Is<object?[]>(args => (string)args[0]! == "cam-1"),
            default));
    }

    [Fact]
    public async Task OnDisconnected_Display_NotifiesAllCameras()
    {
        _state.TrySetDisplay("display-1");
        _state.TryAddCamera("cam-conn-1");
        _state.TryAddCamera("cam-conn-2");

        var cam1Proxy = SetupClientProxy("cam-conn-1");
        var cam2Proxy = SetupClientProxy("cam-conn-2");

        SetConnectionId("display-1");

        await _hub.OnDisconnectedAsync(null);

        cam1Proxy.Verify(p => p.SendCoreAsync("SessionEnded", It.IsAny<object?[]>(), default));
        cam2Proxy.Verify(p => p.SendCoreAsync("SessionEnded", It.IsAny<object?[]>(), default));
        Assert.Null(_state.DisplayConnectionId);
        Assert.Equal(0, _state.ActiveCameraCount);
    }

    [Fact]
    public async Task SendOffer_RelaysToCorrectCamera()
    {
        _state.TrySetDisplay("display-1");
        _state.TryAddCamera("cam-conn-1");
        var camProxy = SetupClientProxy("cam-conn-1");
        SetConnectionId("display-1");

        await _hub.SendOffer("cam-1", "sdp-offer");

        camProxy.Verify(p => p.SendCoreAsync(
            "ReceiveOffer",
            It.Is<object?[]>(args => (string)args[0]! == "cam-1" && (string)args[1]! == "sdp-offer"),
            default));
    }

    [Fact]
    public async Task SendAnswer_RelaysToDisplay()
    {
        _state.TrySetDisplay("display-1");
        var displayProxy = SetupClientProxy("display-1");
        _state.TryAddCamera("cam-conn-1");
        SetConnectionId("cam-conn-1");

        await _hub.SendAnswer("cam-1", "sdp-answer");

        displayProxy.Verify(p => p.SendCoreAsync(
            "ReceiveAnswer",
            It.Is<object?[]>(args => (string)args[0]! == "cam-1" && (string)args[1]! == "sdp-answer"),
            default));
    }

    [Fact]
    public async Task SendIceCandidate_FromDisplay_RelaysToCam()
    {
        _state.TrySetDisplay("display-1");
        _state.TryAddCamera("cam-conn-1");
        var camProxy = SetupClientProxy("cam-conn-1");
        SetConnectionId("display-1");

        await _hub.SendIceCandidate("cam-1", "ice-candidate", fromDisplay: true);

        camProxy.Verify(p => p.SendCoreAsync(
            "ReceiveIceCandidate",
            It.Is<object?[]>(args => (string)args[0]! == "cam-1" && (string)args[1]! == "ice-candidate"),
            default));
    }

    [Fact]
    public async Task SendIceCandidate_FromCamera_RelaysToDisplay()
    {
        _state.TrySetDisplay("display-1");
        var displayProxy = SetupClientProxy("display-1");
        _state.TryAddCamera("cam-conn-1");
        SetConnectionId("cam-conn-1");

        await _hub.SendIceCandidate("cam-1", "ice-candidate", fromDisplay: false);

        displayProxy.Verify(p => p.SendCoreAsync(
            "ReceiveIceCandidate",
            It.Is<object?[]>(args => (string)args[0]! == "cam-1" && (string)args[1]! == "ice-candidate"),
            default));
    }
}
