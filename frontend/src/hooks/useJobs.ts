import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jobsApi } from "@/api/endpoints";

export function useJobs(projectId: string) {
  return useQuery({
    queryKey: ["jobs", projectId, "list"],
    queryFn: () => jobsApi.list(projectId, { page_size: 20 } as any),
    enabled: !!projectId,
    refetchInterval: 5_000,
  });
}

export function useActiveJob(projectId: string) {
  return useQuery({
    queryKey: ["jobs", projectId, "active"],
    queryFn: () => jobsApi.getActive(projectId),
    enabled: !!projectId,
    refetchInterval: 3_000,
  });
}

export function useCancelJob(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => jobsApi.cancel(projectId, jobId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs", projectId] }),
  });
}
