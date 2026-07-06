import type { Metadata } from "next";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v13-appRouter";
import ThemeRegistry from "@/components/ThemeRegistry";
import { RoleProvider } from "@/context/RoleContext";

export const metadata: Metadata = {
  title: "Assignment Dashboard",
  description: "Assignment Visibility & Resource Alignment Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppRouterCacheProvider>
          <ThemeRegistry>
            <RoleProvider>{children}</RoleProvider>
          </ThemeRegistry>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
