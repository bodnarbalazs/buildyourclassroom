using System.Collections.Concurrent;

namespace Hackathon.Api.Hubs;

public class LiveFeedState
{
    private readonly ConcurrentDictionary<string, string> _cameras = new(); // cameraId → connectionId
    private readonly object _lock = new();

    public string? DisplayConnectionId { get; private set; }

    public (bool Success, string? CameraId) TryAddCamera(string connectionId)
    {
        lock (_lock)
        {
            if (_cameras.Count >= 4)
                return (false, null);

            var cameraId = NextAvailableId();
            _cameras[cameraId] = connectionId;
            return (true, cameraId);
        }
    }

    public string? RemoveByConnectionId(string connectionId)
    {
        var entry = _cameras.FirstOrDefault(kvp => kvp.Value == connectionId);
        if (entry.Key is null) return null;
        _cameras.TryRemove(entry.Key, out _);
        return entry.Key;
    }

    public void TrySetDisplay(string connectionId)
    {
        DisplayConnectionId = connectionId;
    }

    public void ClearDisplay()
    {
        DisplayConnectionId = null;
    }

    public bool IsDisplay(string connectionId) => DisplayConnectionId == connectionId;

    public string? GetCameraConnectionId(string cameraId)
    {
        return _cameras.TryGetValue(cameraId, out var connId) ? connId : null;
    }

    public int ActiveCameraCount => _cameras.Count;

    public IReadOnlyCollection<string> CameraConnectionIds => _cameras.Values.ToList();

    public void Clear()
    {
        DisplayConnectionId = null;
        _cameras.Clear();
    }

    private string NextAvailableId()
    {
        for (var i = 1; i <= 4; i++)
        {
            var id = $"cam-{i}";
            if (!_cameras.ContainsKey(id))
                return id;
        }

        // Should never reach here — caller checks count < 4
        throw new InvalidOperationException("No camera slot available");
    }
}
