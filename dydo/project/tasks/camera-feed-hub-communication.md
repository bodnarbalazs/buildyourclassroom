---
area: general
name: camera-feed-hub-communication
status: human-reviewed
created: 2026-02-28T07:00:57.7847260Z
assigned: Iris
updated: 2026-02-28T07:11:54.2393810Z
---

# Task: camera-feed-hub-communication

(No description)

## Progress

- [ ] (Not started)

## Files Changed

(None yet)

## Review Summary

Fixed two bugs in live camera feed WebRTC communication: (1) CRITICAL — useLiveFeedHub returned a new object every render, causing all WebRTC peer connections to be destroyed on every re-render. Fixed by wrapping return in useMemo. (2) MODERATE — Race condition where JoinAsDisplay/JoinAsCamera was invoked before consumer hooks registered their SignalR handlers, causing CameraJoined events to be lost. Fixed by moving join invocations from useLiveFeedHub into useWebRTCSender/useWebRTCReceivers (after handler registration). All 71 frontend tests pass. No plan deviations — followed Grace's investigation recommendations.

## Code Review

- Reviewed by: Emma
- Date: 2026-02-28 07:14
- Result: PASSED
- Notes: LGTM. Both bugs fixed correctly: (1) useMemo stabilizes the hub return object — deps are [state, on, off, invoke] where on/off/invoke are all useCallback([], []) making them stable; connectionRef.current is valid by the time state reaches 'connected'. (2) Join calls moved into useWebRTCSender/useWebRTCReceivers after handler registration, eliminating the race condition. Track cleanup added in cleanupCamera and effect teardown. Camera error handling improved with proper DOMException discrimination. OverlayCanvas early return on zero videoWidth is cleaner than fallback scale. All 71 tests pass.

Awaiting human approval.