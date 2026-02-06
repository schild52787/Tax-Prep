import api from './client';
import type { TaxReturn, TaxReturnCreate, TaxReturnUpdate } from '../types/taxReturn';

export async function listReturns(): Promise<TaxReturn[]> {
  const { data } = await api.get('/returns/');
  return data;
}

export async function createReturn(payload: TaxReturnCreate): Promise<TaxReturn> {
  const { data } = await api.post('/returns/', payload);
  return data;
}

export async function getReturn(id: string): Promise<TaxReturn> {
  const { data } = await api.get(`/returns/${id}`);
  return data;
}

export async function updateReturn(id: string, payload: TaxReturnUpdate): Promise<TaxReturn> {
  const { data } = await api.patch(`/returns/${id}`, payload);
  return data;
}

export async function deleteReturn(id: string): Promise<void> {
  await api.delete(`/returns/${id}`);
}
