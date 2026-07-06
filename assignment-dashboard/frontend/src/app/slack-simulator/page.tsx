"use client";
import AppShell from "@/components/AppShell";
import SlackSimulator from "@/components/SlackSimulator";
import { Box, Typography } from "@mui/material";

export default function SlackSimulatorPage() {
  return (
    <AppShell>
      <Box sx={{ maxWidth: 800, mx: "auto" }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
          Slack Simulator
        </Typography>
        <SlackSimulator onProjectCreated={() => {}} />
      </Box>
    </AppShell>
  );
}
