"use client";
import { createTheme, ThemeProvider, CssBaseline } from "@mui/material";
import React from "react";

const theme = createTheme({
  palette: {
    primary: { main: "#3b82d4" },
    secondary: { main: "#7c5cd8" },
    background: { default: "#f7f8fa" },
  },
  typography: {
    fontFamily: '-apple-system, "Segoe UI", system-ui, sans-serif',
    fontSize: 14,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: { body: { backgroundColor: "#f7f8fa" } },
    },
  },
});

export default function ThemeRegistry({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}
