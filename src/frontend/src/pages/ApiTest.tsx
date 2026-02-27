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
    <div className="max-w-4xl mx-auto py-10 px-4 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">API Test Page</h1>

      {/* Auth Section */}
      <section className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        <h2 className="text-xl font-semibold">Authentication</h2>
        <p className="text-sm text-gray-600">
          {isAuthenticated ? "You are logged in." : "You are not logged in."}
        </p>
        <RegisterForm />
      </section>

      {/* Test Buttons */}
      <section className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        <h2 className="text-xl font-semibold">API Endpoints</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <button
              onClick={handleTest}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded hover:bg-gray-900"
            >
              Test
            </button>
            {testResult && (
              <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-40">
                {testResult}
              </pre>
            )}
          </div>

          <div className="space-y-2">
            <button
              onClick={handleAuth}
              className="w-full bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
            >
              Auth
            </button>
            {authResult && (
              <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-40">
                {authResult}
              </pre>
            )}
          </div>

          <div className="space-y-2">
            <button
              onClick={handleMicro}
              className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
            >
              Micro
            </button>
            {microResult && (
              <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-40">
                {microResult}
              </pre>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
