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
          className="border rounded px-3 py-1.5 text-sm"
        />
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="border rounded px-3 py-1.5 text-sm"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="border rounded px-3 py-1.5 text-sm"
        />
        <button
          type="submit"
          disabled={register.isPending}
          className="bg-green-600 text-white px-4 py-1.5 rounded text-sm hover:bg-green-700 disabled:opacity-50"
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
