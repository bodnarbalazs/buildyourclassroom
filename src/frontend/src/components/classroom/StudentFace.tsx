import React from "react";
import type { Emotion } from "../../types/simulation";

import eyeNatural   from "../../assets/faces/Eye_Natural.svg";
import eyeHappy     from "../../assets/faces/Eye_Happy.svg";
import eyeAngry     from "../../assets/faces/Eye_Angry.svg";
import browNeutral  from "../../assets/faces/Eyebrows_Neutral.svg";
import browConfused from "../../assets/faces/Eyebrows_Confused.svg";
import browSad      from "../../assets/faces/Eyebrows_Sad.svg";
import mouthNeutral from "../../assets/faces/Mouth_neutral.svg";
import mouthSmile   from "../../assets/faces/Mouth_Smile.svg";
import mouthBig     from "../../assets/faces/Mouth_BigSmile.svg";
import mouthSad     from "../../assets/faces/Mouth_Sad.svg";
import hair0 from "../../assets/faces/Hair_man1.svg";
import hair1 from "../../assets/faces/Hair_man2.svg";
import hair2 from "../../assets/faces/Hair_Man3.svg";
import hair3 from "../../assets/faces/Hair_man4.svg";
import hair4 from "../../assets/faces/Hair_woman1.svg";
import hair5 from "../../assets/faces/Hair_woman2.svg";
import hair6 from "../../assets/faces/Hair_woman3.svg";
import hair7 from "../../assets/faces/Hair_woman4.svg";
import headBase from "../../assets/faces/Head.svg";

const HAIRS = [hair0, hair1, hair2, hair3, hair4, hair5, hair6, hair7];

export const EMOTION_COLORS: Record<Emotion, string> = {
  neutral:  "#94a3b8",
  focused:  "#4ade80",
  bored:    "#fb923c",
  confused: "#c084fc",
  excited:  "#facc15",
  sleepy:   "#7dd3fc",
};

const PARTS = {
  neutral:  { eye: eyeNatural,  brow: browNeutral,  mouth: mouthNeutral },
  focused:  { eye: eyeNatural,  brow: browNeutral,  mouth: mouthSmile   },
  bored:    { eye: eyeNatural,  brow: browSad,      mouth: mouthSad     },
  confused: { eye: eyeNatural,  brow: browConfused, mouth: mouthNeutral },
  excited:  { eye: eyeHappy,    brow: browNeutral,  mouth: mouthBig     },
  sleepy:   { eye: eyeAngry,    brow: browSad,      mouth: mouthNeutral },
};

interface Props {
  emotion: Emotion;
  studentId?: number;
  className?: string;
}

export default function StudentFace({ emotion, studentId = 0, className }: Props) {
  const hair = HAIRS[studentId % HAIRS.length];
  const { eye, brow, mouth } = PARTS[emotion];
  const d = "385";
  return React.createElement(
    "svg",
    { className, viewBox: "55 50 280 280", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("image", { href: headBase, x: "0", y: "0", width: d, height: d }),
    React.createElement("image", { href: hair,  x: "0", y: "0", width: d, height: d }),
    React.createElement("image", { href: brow,  x: "0", y: "0", width: d, height: d }),
    React.createElement("image", { href: eye,   x: "0", y: "0", width: d, height: d }),
    React.createElement("image", { href: mouth, x: "0", y: "0", width: d, height: d })
  );
}
