import api from './client';
import type { W2Income, Interest1099, Dividend1099, CapitalAssetSale } from '../types/income';

// W-2
export async function listW2s(returnId: string): Promise<W2Income[]> {
  const { data } = await api.get(`/returns/${returnId}/income/w2`);
  return data;
}

export async function createW2(returnId: string, payload: Partial<W2Income>): Promise<W2Income> {
  const { data } = await api.post(`/returns/${returnId}/income/w2`, payload);
  return data;
}

export async function updateW2(returnId: string, w2Id: string, payload: Partial<W2Income>): Promise<W2Income> {
  const { data } = await api.put(`/returns/${returnId}/income/w2/${w2Id}`, payload);
  return data;
}

export async function deleteW2(returnId: string, w2Id: string): Promise<void> {
  await api.delete(`/returns/${returnId}/income/w2/${w2Id}`);
}

// 1099-INT
export async function listInterest1099s(returnId: string): Promise<Interest1099[]> {
  const { data } = await api.get(`/returns/${returnId}/income/1099-int`);
  return data;
}

export async function createInterest1099(returnId: string, payload: Partial<Interest1099>): Promise<Interest1099> {
  const { data } = await api.post(`/returns/${returnId}/income/1099-int`, payload);
  return data;
}

// 1099-DIV
export async function listDividend1099s(returnId: string): Promise<Dividend1099[]> {
  const { data } = await api.get(`/returns/${returnId}/income/1099-div`);
  return data;
}

export async function createDividend1099(returnId: string, payload: Partial<Dividend1099>): Promise<Dividend1099> {
  const { data } = await api.post(`/returns/${returnId}/income/1099-div`, payload);
  return data;
}

// Capital Sales
export async function listCapitalSales(returnId: string): Promise<CapitalAssetSale[]> {
  const { data } = await api.get(`/returns/${returnId}/income/capital-sales`);
  return data;
}

export async function createCapitalSale(returnId: string, payload: Partial<CapitalAssetSale>): Promise<CapitalAssetSale> {
  const { data } = await api.post(`/returns/${returnId}/income/capital-sales`, payload);
  return data;
}
