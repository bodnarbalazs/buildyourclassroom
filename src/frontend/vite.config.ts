import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: parseInt(process.env.PORT || "5069"),
    proxy: {
      "/api": {
        target:
          process.env.services__api__https__0 ||
          process.env.services__api__http__0 ||
          "https://localhost:5421",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
