import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-IN').format(value);
}

export function getStockStatusColor(status: string): string {
  switch (status) {
    case 'IN_STOCK': return 'badge-green';
    case 'LOW_STOCK': return 'badge-yellow';
    case 'OUT_OF_STOCK': return 'badge-red';
    default: return 'badge-blue';
  }
}

export function getStockStatusLabel(status: string): string {
  switch (status) {
    case 'IN_STOCK': return 'In Stock';
    case 'LOW_STOCK': return 'Low Stock';
    case 'OUT_OF_STOCK': return 'Out of Stock';
    default: return status;
  }
}

export function getApiErrorMessage(error: unknown): string {
  if (error && typeof error === 'object') {
    const err = error as { response?: { data?: { detail?: string } } };
    if (err.response?.data?.detail) return err.response.data.detail;
    const msgErr = error as { message?: string };
    if (msgErr.message) return msgErr.message;
  }
  return 'An unexpected error occurred. Please try again.';
}

export function downloadCSV(data: object[], filename: string) {
  if (!data.length) return;
  const keys = Object.keys(data[0]);
  const csvContent = [
    keys.join(','),
    ...data.map(row =>
      keys.map(k => {
        const val = (row as Record<string, unknown>)[k];
        const str = String(val ?? '').replace(/"/g, '""');
        return `"${str}"`;
      }).join(',')
    )
  ].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
