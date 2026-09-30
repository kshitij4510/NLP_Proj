import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/api/endpoints";
import { useAuthStore } from "@/lib/store";

export function useLogin() {
  const navigate = useNavigate();
  const { setTokens } = useAuthStore();
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      navigate("/dashboard");
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();
  return useMutation({
    mutationFn: authApi.register,
    onSuccess: () => navigate("/login"),
  });
}

export function useLogout() {
  const { clearTokens } = useAuthStore();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  return () => {
    clearTokens();
    queryClient.clear();
    navigate("/login");
  };
}
