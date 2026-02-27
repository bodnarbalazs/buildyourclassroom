import type { Emotion } from "../../types/simulation";

// South Park-style flat cartoon face. Eyes and mouth shape encode the emotion.
interface Props {
  emotion: Emotion;
  size?: number;
}

const SKIN = "#FDDBB4";
const INK = "#333";

function Eyes({ emotion }: { emotion: Emotion }) {
  if (emotion === "sleepy" || emotion === "bored") {
    return (
      <>
        <path d="M9 13 Q11 11 13 13" stroke={INK} strokeWidth="1.5" fill="none" strokeLinecap="round" />
        <path d="M19 13 Q21 11 23 13" stroke={INK} strokeWidth="1.5" fill="none" strokeLinecap="round" />
      </>
    );
  }
  const r = emotion === "excited" || emotion === "confused" ? 2.5 : 2;
  return (
    <>
      <circle cx="11" cy="13" r={r} fill={INK} />
      <circle cx="21" cy="13" r={r} fill={INK} />
    </>
  );
}

function Mouth({ emotion }: { emotion: Emotion }) {
  switch (emotion) {
    case "focused":
      return <path d="M12 21 L20 21" stroke={INK} strokeWidth="1.5" fill="none" strokeLinecap="round" />;
    case "excited":
      return <path d="M10 19 Q16 25 22 19" stroke={INK} strokeWidth="1.5" fill="none" strokeLinecap="round" />;
    case "bored":
      return <path d="M11 22 Q16 19 21 22" stroke={INK} strokeWidth="1.5" fill="none" strokeLinecap="round" />;
    case "confused":
      return <path d="M11 21 Q14 18 16 21 Q18 24 21 21" stroke={INK} strokeWidth="1.5" fill="none" strokeLinecap="round" />;
    case "sleepy":
      return <path d="M13 22 Q16 24 19 22" stroke={INK} strokeWidth="1.5" fill="none" strokeLinecap="round" />;
    default:
      return <path d="M12 21 Q16 23 20 21" stroke={INK} strokeWidth="1.5" fill="none" strokeLinecap="round" />;
  }
}

export default function StudentFace({ emotion, size = 32 }: Props) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <circle cx="16" cy="16" r="14" fill={SKIN} stroke={INK} strokeWidth="1.5" />
      <Eyes emotion={emotion} />
      <Mouth emotion={emotion} />
    </svg>
  );
}
