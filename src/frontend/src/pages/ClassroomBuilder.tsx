import { useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { notifyUnauthorized } from "../api/unauthorizedBus";

export default function ClassroomBuilder() {
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) notifyUnauthorized();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-gray-500">Please log in to access the Classroom Builder.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-10 px-4">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Classroom Builder</h1>
      <p className="text-gray-600">Build and configure your classroom here.</p>
    </div>
  );
}
