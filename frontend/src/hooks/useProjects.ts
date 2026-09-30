import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsApi, researchApi } from "@/api/endpoints";

export const projectKeys = {
  all: ["projects"] as const,
  list: (params?: object) => [...projectKeys.all, "list", params] as const,
  detail: (id: string) => [...projectKeys.all, "detail", id] as const,
  summary: (id: string) => [...projectKeys.all, "summary", id] as const,
};

export function useProjects(params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => projectsApi.list(params),
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  });
}

export function useProjectSummary(id: string) {
  return useQuery({
    queryKey: projectKeys.summary(id),
    queryFn: () => researchApi.getSummary(id),
    enabled: !!id,
    refetchInterval: 30_000,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: projectKeys.all }),
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: projectKeys.all }),
  });
}

export function useTriggerPipeline(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (stage?: string) => researchApi.triggerPipeline(projectId, stage as any),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs", projectId] });
      qc.invalidateQueries({ queryKey: projectKeys.summary(projectId) });
    },
  });
}
