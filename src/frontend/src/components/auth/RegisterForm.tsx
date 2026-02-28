import { useState } from "react";
import { useRegisterMutation } from "../../hooks/useAuthMutations";

export default function RegisterForm() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const register = useRegisterMutation();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    register.mutate(
      { email, username, password },
      {
        onSuccess: () => {
          setEmail("");
          setUsername("");
          setPassword("");
        },
      },
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="font-medium text-gray-700">Register</h3>
      <form onSubmit={handleSubmit} className="flex gap-2 flex-wrap">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={register.isPending}
          className="rounded-lg bg-green-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
        >
          {register.isPending ? "Registering..." : "Register"}
        </button>
      </form>
      {register.isError && (
        <p className="text-sm text-red-600">{register.error.message}</p>
      )}
      {register.isSuccess && (
        <p className="text-sm text-green-600">Registered successfully!</p>
      )}
    </div>
  );
}
