import { useState, useEffect } from "react";
import { subscribeUnauthorized } from "../../api/unauthorizedBus";
import { useAuth } from "../../hooks/useAuth";
import LoginModal from "./LoginModal";

export default function UnauthorizedModalHost() {
  const [open, setOpen] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    return subscribeUnauthorized(() => setOpen(true));
  }, []);

  // Auto-close when user re-authenticates
  useEffect(() => {
    if (isAuthenticated) setOpen(false);
  }, [isAuthenticated]);

  return <LoginModal open={open} onClose={() => setOpen(false)} />;
}
