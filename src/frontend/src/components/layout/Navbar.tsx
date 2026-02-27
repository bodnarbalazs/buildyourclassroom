import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { useLogoutMutation } from "../../hooks/useAuthMutations";

export default function Navbar() {
  const { user, isAuthenticated } = useAuth();
  const logout = useLogoutMutation();

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6">
      <span className="text-lg font-bold text-gray-900">Hackathon</span>
      <Link to="/" className="text-gray-600 hover:text-gray-900">
        Home
      </Link>
      <Link to="/api-test" className="text-gray-600 hover:text-gray-900">
        API Test
      </Link>
      <Link to="/classroom-builder" className="text-gray-600 hover:text-gray-900">
        Classroom Builder
      </Link>
      <div className="ml-auto flex items-center gap-4">
        {isAuthenticated ? (
          <>
            <span className="text-sm text-gray-700">{user!.username}</span>
            <button
              onClick={() => logout.mutate()}
              className="text-sm text-red-600 hover:text-red-800"
            >
              Logout
            </button>
          </>
        ) : (
          <span className="text-sm text-gray-400">Not logged in</span>
        )}
      </div>
    </nav>
  );
}
