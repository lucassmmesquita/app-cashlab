/**
 * CashLab — Hook para upload de fatura
 */
import { useState } from 'react';
import { invoiceService, type UploadPreview } from '../services/invoiceService';

export function useInvoiceUpload() {
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const upload = async (fileUri: string, fileName: string, bank: string = 'auto') => {
    try {
      setIsUploading(true);
      setError(null);
      const result = await invoiceService.upload(fileUri, fileName, bank);
      setPreview(result);
      return result;
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Erro ao enviar fatura');
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const reset = () => {
    setPreview(null);
    setError(null);
  };

  return { upload, isUploading, preview, error, reset };
}
