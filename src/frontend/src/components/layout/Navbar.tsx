import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { useLogoutMutation } from "../../hooks/useAuthMutations";

const NAV_LINKS = [
  { to: "/", label: "Home" },
  { to: "/api-test", label: "API Test" },
  { to: "/classroom-builder", label: "Classroom Builder" },
  { to: "/test-generator", label: "Test Generator" },
  { to: "/class-evaluation", label: "Class Evaluation" },
  { to: "/research", label: "Research" },
] as const;

export default function Navbar() {
  const { user, isAuthenticated } = useAuth();
  const logout = useLogoutMutation();
  const [menuOpen, setMenuOpen] = useState(false);

  const userSection = isAuthenticated ? (
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
  );

  return (
    <nav className="bg-white border-b border-gray-200 px-4 md:px-6 py-3">
      <div className="flex items-center justify-between">
        <span className="text-lg font-bold text-gray-900">Hackathon</span>

        <button
          className="md:hidden text-gray-600 hover:text-gray-900 text-2xl leading-none"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? "\u2715" : "\u2630"}
        </button>

        <div className="hidden md:flex items-center gap-6 ml-6 flex-1">
          {NAV_LINKS.map((link) => (
            <Link key={link.to} to={link.to} className="text-gray-600 hover:text-gray-900">
              {link.label}
            </Link>
          ))}
          <div className="ml-auto flex items-center gap-4">{userSection}</div>
        </div>
      </div>

      {menuOpen && (
        <div className="md:hidden flex flex-col gap-2 pt-3 pb-2 z-40">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="text-gray-600 hover:text-gray-900 py-1"
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="flex items-center gap-4 pt-2 border-t border-gray-100">
            {userSection}
          </div>
        </div>
      )}
    </nav>
  );
}
