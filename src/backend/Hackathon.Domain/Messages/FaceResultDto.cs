namespace Hackathon.Domain.Messages;

public record FaceResultDto(
    int FaceIndex,
    BboxDto Bbox,
    string DominantEmotion,
    IReadOnlyDictionary<string, double> EmotionScores,
    string EngagementLevel,
    double EngagementScore);
