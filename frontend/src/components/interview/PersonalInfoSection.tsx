import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../api/client';

interface TaxpayerForm {
  first_name: string;
  middle_initial: string;
  last_name: string;
  ssn: string;
  occupation: string;
  street_address: string;
  apt_number: string;
  city: string;
  state: string;
  zip_code: string;
}

interface Props {
  returnId: string;
  onNext: () => void;
}

export function PersonalInfoSection({ returnId, onNext }: Props) {
  const queryClient = useQueryClient();

  const { data: existing } = useQuery({
    queryKey: ['taxpayer', returnId, 'primary'],
    queryFn: async () => {
      try {
        const { data } = await api.get(`/returns/${returnId}/taxpayer/primary`);
        return data;
      } catch {
        return null;
      }
    },
  });

  const { register, handleSubmit, formState: { errors } } = useForm<TaxpayerForm>({
    values: existing ?? undefined,
  });

  const saveMutation = useMutation({
    mutationFn: (data: TaxpayerForm) =>
      api.put(`/returns/${returnId}/taxpayer/primary`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['taxpayer', returnId] });
      onNext();
    },
  });

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 mb-1">Personal Information</h2>
      <p className="text-sm text-gray-500 mb-6">
        Enter your name, Social Security number, and address as they appear on your tax documents.
      </p>

      <form onSubmit={handleSubmit((data) => saveMutation.mutate(data))} className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
            <input
              {...register('first_name', { required: 'Required' })}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
            {errors.first_name && <p className="text-xs text-danger mt-1">{errors.first_name.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">M.I.</label>
            <input
              {...register('middle_initial')}
              maxLength={1}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
            <input
              {...register('last_name', { required: 'Required' })}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
            {errors.last_name && <p className="text-xs text-danger mt-1">{errors.last_name.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Social Security Number *</label>
            <input
              {...register('ssn', { required: 'Required' })}
              placeholder="XXX-XX-XXXX"
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Occupation</label>
            <input
              {...register('occupation')}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
        </div>

        <hr className="border-border" />
        <h3 className="font-medium text-gray-700">Mailing Address</h3>

        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Street Address</label>
            <input
              {...register('street_address')}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Apt #</label>
            <input
              {...register('apt_number')}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
            <input
              {...register('city')}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
            <input
              {...register('state')}
              maxLength={2}
              placeholder="e.g. CA"
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ZIP Code</label>
            <input
              {...register('zip_code')}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="bg-accent text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors"
          >
            {saveMutation.isPending ? 'Saving...' : 'Save & Continue'}
          </button>
        </div>
      </form>
    </div>
  );
}
