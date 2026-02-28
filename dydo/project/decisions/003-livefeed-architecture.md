---
type: decision
status: accepted
date: 2026-02-28
area: feature
---

# 003 — Livefeed Multi-Camera Architecture

Real-time multi-camera classroom attention analysis. Up to 4 phones stream video via WebRTC to a display page, which extracts snapshots for DeepFace analysis and renders bounding box overlays with a collective attention score.

## Context

We need a "wow factor" demo feature: point phones at the audience and show a live feed on the projector with AI-detected face rectangles and an attention meter. Must handle multiple camera angles (up to 4), be smooth (not a slideshow), and use the existing DeepFace emotion analysis pipeline.

## Decision

### Video Transport: WebRTC Peer-to-Peer (Phone → Display)

Phones stream directly to the display browser via WebRTC. The backend **never touches video data** — only relays tiny signaling messages (SDP offers/answers, ICE candidates) via a SignalR hub.

**Why not proxy through backend?** Unnecessary complexity, adds latency, burns server bandwidth. WebRTC P2P over LAN gives sub-millisecond latency with zero backend load.

**Why not snapshot-only (no WebRTC)?** Choppy. Even at 5fps, a JPEG slideshow doesn't read as "live" in a demo.

### Signaling: SignalR Hub (Single Session)

A lightweight SignalR hub in the .NET API relays WebRTC signaling. In-memory state only — no persistence needed.

**Single session design:** There is one global live session at a time. The display page owns it. No session IDs in URLs, no multi-session routing. The display opens `/livefeed/display`, phones open `/livefeed/camera`. Simpler, fewer failure modes, and we control the phones ourselves (no QR codes for random audience members).

**4-camera hard cap:** The 5th phone gets a clean rejection message. Star topology (all phones → display) works well for 4 peers. Beyond that you'd need an SFU media server, which is out of scope.

### Analysis: Display-Side Snapshot Extraction

The **display** (not the phones) grabs JPEG frames from each video feed and POSTs them to the existing `/emotion/sessions/{id}/snapshots` endpoint. This means:

- Phones are dumb cameras — stream and nothing else
- No dual upload concern (streaming + JPEG) on phones
- The existing DeepFace pipeline is completely unchanged
- Snapshots are staggered: one camera analyzed every 250ms, so each camera updates every ~1 second

### Overlay: Client-Side Canvas

The display renders each video in a `<video>` element with an absolutely-positioned `<canvas>` on top. The canvas draws bounding boxes and emotion labels from the latest analysis result. The video is smooth (30fps WebRTC); the overlays update at ~1fps. This reads as "AI analyzing in real-time" rather than laggy.

### STUN/TURN

Google's public STUN server (`stun:stun.l.google.com:19302`) for ICE discovery. No TURN server — the demo runs on the same LAN. If NAT traversal fails, phones and display must be on the same WiFi network.

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| WebRTC via SFU (mediasoup/Janus) | Way too complex for a hackathon. P2P handles 4 peers fine. |
| Snapshot-only (no live video) | Doesn't look "live." Demo impact suffers. |
| Phone uploads snapshots + streams | Dual duty on phone, potential stream lag. Display-side extraction is cleaner. |
| Multi-session support | Unnecessary complexity. One session is all we need for the demo. |
| QR code for phone joining | Risk of audience overwhelming the system. We handle phones ourselves. |

## Consequences

- WebRTC requires same-network for reliable P2P (acceptable for demo)
- Display browser does all the heavy lifting (WebRTC receiving, snapshot extraction, overlay rendering) — needs a decent laptop
- Camera page must handle iOS Safari WebRTC quirks (tested separately)
- The 4-camera limit is a hard architectural constraint of the star topology
