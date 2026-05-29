import dayjs from 'dayjs';
import { RiskLevel } from '../types';
import { RISK_COLORS } from '../constants';

export function formatDate(dateStr: string, format = 'DD MMM YYYY'): string {
  return dayjs(dateStr).format(format);
}

export function formatPercentage(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function getAttendanceColor(percentage: number): string {
  if (percentage >= 85) return '#22c55e';
  if (percentage >= 75) return '#f59e0b';
  return '#ef4444';
}

export function getRiskColor(level: RiskLevel): string {
  return RISK_COLORS[level];
}

export function getRiskBadgeStyle(level: RiskLevel): { bg: string; text: string } {
  const map: Record<RiskLevel, { bg: string; text: string }> = {
    LOW:      { bg: '#dcfce7', text: '#166534' },
    MEDIUM:   { bg: '#fef9c3', text: '#854d0e' },
    HIGH:     { bg: '#ffedd5', text: '#9a3412' },
    CRITICAL: { bg: '#fee2e2', text: '#991b1b' },
  };
  return map[level];
}

export function getGradeColor(grade: string): string {
  const map: Record<string, string> = {
    'A+': '#16a34a', A: '#22c55e', 'B+': '#65a30d',
    B: '#ca8a04', C: '#ea580c', D: '#dc2626', F: '#7f1d1d',
  };
  return map[grade] ?? '#6b7280';
}

export function truncate(text: string, maxLength: number): string {
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text;
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((n) => n[0]?.toUpperCase() ?? '')
    .join('');
}

export function pluralize(count: number, singular: string, plural?: string): string {
  const word = count === 1 ? singular : (plural ?? `${singular}s`);
  return `${count} ${word}`;
}

export function isToday(dateStr: string): boolean {
  return dayjs(dateStr).isSame(dayjs(), 'day');
}

export function todayISO(): string {
  return dayjs().format('YYYY-MM-DD');
}

export function monthStartISO(): string {
  return dayjs().startOf('month').format('YYYY-MM-DD');
}
