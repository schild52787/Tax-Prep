import api from './client';
import type { CalculationResult } from '../types/calculation';

export async function runCalculation(returnId: string): Promise<CalculationResult> {
  const { data } = await api.post(`/returns/${returnId}/calculate`);
  return data;
}

export async function getCalculation(returnId: string): Promise<CalculationResult> {
  const { data } = await api.get(`/returns/${returnId}/calculation`);
  return data;
}

export function getFormsPdfUrl(returnId: string): string {
  return `/api/v1/returns/${returnId}/pdf/forms`;
}

export function getSummaryPdfUrl(returnId: string): string {
  return `/api/v1/returns/${returnId}/pdf/summary`;
}
