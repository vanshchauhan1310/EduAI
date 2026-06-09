import React, { useMemo } from 'react';
import Markdown from 'react-native-markdown-display';
import { Colors, Typography, Spacing } from '../../theme';

// Renders an AI tutor answer with markdown (**bold**, lists) using native RN
// components — so the chat bubble keeps sizing/wrapping exactly like a plain
// <Text> did — while converting any LaTeX math (\( \), \[ \], $...$) into
// clean, readable Unicode notation (H₂O, 1/v - 1/u = 1/f, →, ×, …) instead of
// showing raw backslash-commands.

const _SUB_MAP: Record<string, string> = {
  '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
  '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
  a: 'ₐ', e: 'ₑ', o: 'ₒ', x: 'ₓ', h: 'ₕ', k: 'ₖ', l: 'ₗ', m: 'ₘ', n: 'ₙ', p: 'ₚ', s: 'ₛ', t: 'ₜ',
};
const _SUP_MAP: Record<string, string> = {
  '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
  '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾', n: 'ⁿ', i: 'ⁱ',
};
const _SYMBOL_MAP: [RegExp, string][] = [
  [/\\(?:rightarrow|to|implies|Rightarrow)/g, '→'],
  [/\\leftarrow/g, '←'],
  [/\\leftrightarrow/g, '↔'],
  [/\\times/g, '×'],
  [/\\div/g, '÷'],
  [/\\cdot/g, '·'],
  [/\\pm/g, '±'],
  [/\\approx/g, '≈'],
  [/\\neq/g, '≠'],
  [/\\leq/g, '≤'],
  [/\\geq/g, '≥'],
  [/\\degree/g, '°'],
  [/\\circ/g, '°'],
  [/\\Delta/g, 'Δ'],
  [/\\delta/g, 'δ'],
  [/\\theta/g, 'θ'],
  [/\\lambda/g, 'λ'],
  [/\\mu/g, 'μ'],
  [/\\pi/g, 'π'],
  [/\\Omega/g, 'Ω'],
  [/\\omega/g, 'ω'],
  [/\\alpha/g, 'α'],
  [/\\beta/g, 'β'],
  [/\\infty/g, '∞'],
];

const _FRAC_RE = /\\(?:d|t)?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}/g;
const _SQRT_RE = /\\sqrt\s*\{([^{}]*)\}/g;
const _TEXT_RE = /\\(?:text|mathrm|mathbf)\s*[\{\[]\s*([^}\]]*?)\s*[}\]]/g;
const _SUB_BRACE_RE = /_\{([^{}]*)\}/g;
const _SUP_BRACE_RE = /\^\{([^{}]*)\}/g;
const _SUB_CHAR_RE = /_([A-Za-z0-9+\-])/g;
const _SUP_CHAR_RE = /\^([A-Za-z0-9+\-])/g;
const _CMD_RE = /\\[a-zA-Z]+/g;
const _MATH_BLOCK_RE = /\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\\\(([\s\S]+?)\\\)|\$([^$\n]+?)\$/g;

function mapChars(s: string, map: Record<string, string>): string {
  return s.split('').map((c) => map[c] ?? c).join('');
}

function latexToPlain(tex: string): string {
  let t = tex.trim();
  t = t.replace(_FRAC_RE, '($1)/($2)');
  t = t.replace(_SQRT_RE, '√($1)');
  t = t.replace(_TEXT_RE, '$1');
  for (const [re, sym] of _SYMBOL_MAP) t = t.replace(re, sym);
  t = t.replace(_SUB_BRACE_RE, (_, inner) => mapChars(inner, _SUB_MAP));
  t = t.replace(_SUP_BRACE_RE, (_, inner) => mapChars(inner, _SUP_MAP));
  t = t.replace(_SUB_CHAR_RE, (_, c) => _SUB_MAP[c] ?? c);
  t = t.replace(_SUP_CHAR_RE, (_, c) => _SUP_MAP[c] ?? c);
  t = t.replace(_CMD_RE, '');
  t = t.replace(/[{}]/g, '');
  return t.replace(/\s+/g, ' ').trim();
}

function preprocess(raw: string): string {
  return raw.replace(_MATH_BLOCK_RE, (...args) => {
    const groups = args.slice(1, 5) as (string | undefined)[];
    const inner = groups.find((g) => g !== undefined) ?? '';
    return latexToPlain(inner);
  });
}

const markdownStyles = {
  body: { fontSize: Typography.sizes.sm, color: Colors.neutral[800], lineHeight: 20 },
  paragraph: { marginTop: 0, marginBottom: 6 },
  strong: { fontWeight: Typography.weights.bold as any },
  bullet_list: { marginBottom: 4 },
  ordered_list: { marginBottom: 4 },
  list_item: { marginBottom: 2, flexDirection: 'row' as const },
  heading1: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold as any, marginTop: 6, marginBottom: 4 },
  heading2: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold as any, marginTop: 6, marginBottom: 4 },
  heading3: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold as any, marginTop: 4, marginBottom: 2 },
  code_inline: { backgroundColor: Colors.neutral[100], borderRadius: 4, paddingHorizontal: 4, fontSize: Typography.sizes.sm - 1 },
  code_block: { backgroundColor: Colors.neutral[100], borderRadius: 8, padding: Spacing.sm },
  fence: { backgroundColor: Colors.neutral[100], borderRadius: 8, padding: Spacing.sm },
  link: { color: Colors.secondary[600] },
};

export default function RichAnswer({ text }: { text: string }) {
  const content = useMemo(() => preprocess(text || ''), [text]);
  return <Markdown style={markdownStyles as any}>{content}</Markdown>;
}
