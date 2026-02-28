import { useState, useCallback } from "react";
import { apiFetch } from "../api/apiClient";
import { useAuth } from "../hooks/useAuth";
import RegisterForm from "../components/auth/RegisterForm";

export default function ApiTest() {
  const { isAuthenticated } = useAuth();
  const [testResult, setTestResult] = useState("");
  const [authResult, setAuthResult] = useState("");
  const [microResult, setMicroResult] = useState("");

  const handleTest = useCallback(async () => {
    try {
      const res = await apiFetch("/api/test");
      const data = await res.json();
      setTestResult(JSON.stringify(data, null, 2));
    } catch {
      setTestResult("Error reaching API");
    }
  }, []);

  const handleAuth = useCallback(async () => {
    try {
      const res = await apiFetch("/api/auth/me");
      if (!res.ok) {
        setAuthResult(`${res.status} Unauthorized`);
        return;
      }
      const data = await res.json();
      setAuthResult(JSON.stringify(data, null, 2));
    } catch {
      setAuthResult("Error reaching API");
    }
  }, []);

  const handleMicro = useCallback(async () => {
    try {
      const res = await apiFetch("/api/micro/add", { method: "POST" });
      const data = await res.json();
      setMicroResult(JSON.stringify(data, null, 2));
    } catch {
      setMicroResult("Error reaching API");
    }
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 flex flex-col gap-8">
      <h1 className="text-3xl font-bold text-gray-900">API Test Page</h1>

      {/* Auth Section */}
      <section className="rounded-xl border border-gray-200 bg-gray-50 p-6 flex flex-col gap-4">
        <h2 className="text-lg font-semibold text-gray-900">Authentication</h2>
        <p className="text-sm text-gray-600">
          {isAuthenticated ? "You are logged in." : "You are not logged in."}
        </p>
        <RegisterForm />
      </section>

      {/* Test Buttons */}
      <section className="rounded-xl border border-gray-200 bg-gray-50 p-6 flex flex-col gap-4">
        <h2 className="text-lg font-semibold text-gray-900">API Endpoints</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <button
              onClick={handleTest}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Test
            </button>
            {testResult && (
              <pre className="rounded-lg bg-white border border-gray-200 p-3 text-xs overflow-auto max-h-40">
                {testResult}
              </pre>
            )}
          </div>

          <div className="space-y-2">
            <button
              onClick={handleAuth}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Auth
            </button>
            {authResult && (
              <pre className="rounded-lg bg-white border border-gray-200 p-3 text-xs overflow-auto max-h-40">
                {authResult}
              </pre>
            )}
          </div>

          <div className="space-y-2">
            <button
              onClick={handleMicro}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Micro
            </button>
            {microResult && (
              <pre className="rounded-lg bg-white border border-gray-200 p-3 text-xs overflow-auto max-h-40">
                {microResult}
              </pre>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
