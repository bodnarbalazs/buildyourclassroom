import { useState } from "react";
import { useLoginMutation } from "../../hooks/useAuthMutations";

interface LoginModalProps {
  open: boolean;
  onClose: () => void;
}

export default function LoginModal({ open, onClose }: LoginModalProps) {
  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const login = useLoginMutation();

  if (!open) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    login.mutate(
      { emailOrUsername, password },
      {
        onSuccess: () => {
          setEmailOrUsername("");
          setPassword("");
          onClose();
        },
      },
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Login Required</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl"
            type="button"
          >
            &times;
          </button>
        </div>
        <p className="text-sm text-gray-600">
          Your session has expired. Please log in again.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Email or Username"
            value={emailOrUsername}
            onChange={(e) => setEmailOrUsername(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {login.isError && (
            <p className="text-sm text-red-600">{login.error.message}</p>
          )}
          <button
            type="submit"
            disabled={login.isPending}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {login.isPending ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}
