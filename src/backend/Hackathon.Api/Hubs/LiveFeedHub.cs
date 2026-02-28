using Microsoft.AspNetCore.SignalR;

namespace Hackathon.Api.Hubs;

public class LiveFeedHub(LiveFeedState state) : Hub
{
    public async Task JoinAsDisplay()
    {
        state.TrySetDisplay(Context.ConnectionId);

        // Notify display of any cameras that are already connected (reconnect scenario)
        foreach (var cameraId in GetActiveCameraIds())
        {
            await Clients.Caller.SendAsync("CameraJoined", cameraId);
        }
    }

    public async Task JoinAsCamera()
    {
        if (state.DisplayConnectionId is null)
        {
            await Clients.Caller.SendAsync("CameraRejected", "No active session");
            return;
        }

        var (ok, cameraId) = state.TryAddCamera(Context.ConnectionId);
        if (!ok)
        {
            await Clients.Caller.SendAsync("CameraRejected", "4/4 streams active. Please try again later.");
            return;
        }

        await Clients.Client(state.DisplayConnectionId).SendAsync("CameraJoined", cameraId);
    }

    public async Task SendOffer(string cameraId, string sdp)
    {
        if (!state.IsDisplay(Context.ConnectionId)) return;

        var connId = state.GetCameraConnectionId(cameraId);
        if (connId is null) return;

        await Clients.Client(connId).SendAsync("ReceiveOffer", cameraId, sdp);
    }

    public async Task SendAnswer(string cameraId, string sdp)
    {
        if (state.DisplayConnectionId is null) return;

        await Clients.Client(state.DisplayConnectionId).SendAsync("ReceiveAnswer", cameraId, sdp);
    }

    public async Task SendIceCandidate(string cameraId, string candidate, bool fromDisplay)
    {
        if (fromDisplay)
        {
            var connId = state.GetCameraConnectionId(cameraId);
            if (connId is null) return;
            await Clients.Client(connId).SendAsync("ReceiveIceCandidate", cameraId, candidate);
        }
        else
        {
            if (state.DisplayConnectionId is null) return;
            await Clients.Client(state.DisplayConnectionId).SendAsync("ReceiveIceCandidate", cameraId, candidate);
        }
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        if (state.IsDisplay(Context.ConnectionId))
        {
            var cameraConnIds = state.CameraConnectionIds.ToList();
            state.ClearDisplay();

            foreach (var connId in cameraConnIds)
            {
                await Clients.Client(connId).SendAsync("SessionEnded");
            }

            state.Clear();
        }
        else
        {
            var cameraId = state.RemoveByConnectionId(Context.ConnectionId);
            if (cameraId is not null && state.DisplayConnectionId is not null)
            {
                await Clients.Client(state.DisplayConnectionId).SendAsync("CameraLeft", cameraId);
            }
        }

        await base.OnDisconnectedAsync(exception);
    }

    private IEnumerable<string> GetActiveCameraIds()
    {
        // Return camera IDs that have active connections
        for (var i = 1; i <= 4; i++)
        {
            var id = $"cam-{i}";
            if (state.GetCameraConnectionId(id) is not null)
                yield return id;
        }
    }
}
