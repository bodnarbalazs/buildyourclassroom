interface Props {
  text: string;
}

export default function ThoughtBubble({ text }: Props) {
  return (
    <div className="absolute -top-9 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
      <div className="bg-white border border-gray-300 rounded-xl px-2 py-1 text-xs text-gray-700 whitespace-nowrap shadow">
        {text}
      </div>
      <div className="w-2 h-2 bg-white border-b border-r border-gray-300 rotate-45 absolute -bottom-1 left-1/2 -translate-x-1/2" />
    </div>
  );
}
