import React from "react";
import { StyleProp, Text, TextStyle } from "react-native";

type Props = {
  children: string;
  style?: StyleProp<TextStyle>;
  boldStyle?: StyleProp<TextStyle>;
};

type Token = { text: string; bold?: boolean; italic?: boolean; code?: boolean };

// Splits on **bold**, *italic*/_italic_, and `code` without pulling in a full markdown parser.
function tokenize(input: string): Token[] {
  const pattern = /\*\*(.+?)\*\*|`(.+?)`|(?:\*|_)(.+?)(?:\*|_)/g;
  const tokens: Token[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(input))) {
    if (match.index > lastIndex) {
      tokens.push({ text: input.slice(lastIndex, match.index) });
    }
    if (match[1] !== undefined) tokens.push({ text: match[1], bold: true });
    else if (match[2] !== undefined) tokens.push({ text: match[2], code: true });
    else if (match[3] !== undefined) tokens.push({ text: match[3], italic: true });
    lastIndex = pattern.lastIndex;
  }
  if (lastIndex < input.length) tokens.push({ text: input.slice(lastIndex) });
  return tokens;
}

/** Renders a small subset of inline markdown (bold, italic, inline code) as styled Text. */
export function MarkdownText({ children, style, boldStyle }: Props) {
  const tokens = tokenize(children ?? "");
  return (
    <Text style={style}>
      {tokens.map((token, index) => (
        <Text
          key={index}
          style={[
            token.bold ? [{ fontWeight: "800" as const }, boldStyle] : null,
            token.italic ? { fontStyle: "italic" as const } : null,
            token.code ? { fontFamily: "monospace" } : null,
          ]}
        >
          {token.text}
        </Text>
      ))}
    </Text>
  );
}
