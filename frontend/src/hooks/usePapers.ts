import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { papersApi } from "@/api/endpoints";

const paperKeys = {
  all: (projectId: string) => ["papers", projectId] as const,
  list: (projectId: string, params?: object) => [...paperKeys.all(projectId), "list", params] as const,
  detail: (projectId: string, paperId: string) => [...paperKeys.all(projectId), "detail", paperId] as const,
};

export function usePapers(projectId: string, params?: { page?: number; status?: string }) {
  return useQuery({
    queryKey: paperKeys.list(projectId, params),
    queryFn: () => papersApi.list(projectId, params as any),
    enabled: !!projectId,
  });
}

export function usePaper(projectId: string, paperId: string) {
  return useQuery({
    queryKey: paperKeys.detail(projectId, paperId),
    queryFn: () => papersApi.get(projectId, paperId),
    enabled: !!projectId && !!paperId,
  });
}

export function useAddPaper(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { doi?: string; arxiv_id?: string; title?: string }) =>
      papersApi.add(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: paperKeys.all(projectId) }),
  });
}

export function useUploadPaper(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => papersApi.upload(projectId, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: paperKeys.all(projectId) }),
  });
}

export function useDeletePaper(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (paperId: string) => papersApi.delete(projectId, paperId),
    onSuccess: () => qc.invalidateQueries({ queryKey: paperKeys.all(projectId) }),
  });
}
