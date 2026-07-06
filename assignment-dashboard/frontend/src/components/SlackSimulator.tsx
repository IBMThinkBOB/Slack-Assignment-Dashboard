"use client";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert, Avatar, Box, Button, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle,
  Snackbar, TextField, Typography,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";
import { apiFetch } from "@/lib/api";
import { useRole } from "@/context/RoleContext";
import type { SimMessage } from "@/lib/types";

const ADMIN_SAMPLES = [
  "Need a Storage Scale deployment SME for ABC Corp starting next month. 6-week engagement, high priority.",
  "Looking for an AWS architect to support Globex Inc migration — presales opportunity, starts June 15th.",
  "Hey @Adam, JPMC needs a cloud application for their high net worth clients to track expenditures by July 31st",
  "Acme Ltd wants us to build their Kubernetes platform. High priority paid engagement, starts August 1st.",
];

interface Props {
  onProjectCreated?: () => void;
}

function initials(name: string) {
  return name.split(" ").map((p) => p[0]).join("").toUpperCase().slice(0, 2);
}

// ── System message ────────────────────────────────────────────────────────────

function SystemMessage({ text }: { text: string }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "center", my: 1.5 }}>
      <Box
        sx={{
          px: 2, py: 0.75, borderRadius: 4,
          bgcolor: "#f0faf4", border: "1px solid #b7ebd0",
          display: "flex", alignItems: "center", gap: 0.75,
        }}
      >
        <CheckCircleOutlinedIcon sx={{ fontSize: 13, color: "#2eb67d" }} />
        <Typography variant="caption" sx={{ color: "#1a7a4a", fontWeight: 500 }}>
          {text}
        </Typography>
      </Box>
    </Box>
  );
}

// ── Single message bubble ─────────────────────────────────────────────────────

function MessageBubble({
  msg,
  isAdmin,
  currentUserName,
  onClaim,
  onReply,
}: {
  msg: SimMessage;
  isAdmin: boolean;
  currentUserName: string | null;
  onClaim: (eventId: string) => Promise<void>;
  onReply: (msg: SimMessage) => void;
}) {
  const [claiming, setClaiming] = useState(false);

  // "My" messages align right; everything else aligns left
  const isMyMsg = msg.sender === currentUserName && !msg.is_system_msg;
  const alignRight = isMyMsg;
  // A message "has a project" and was not sent by me = it's an assignment post
  const isAssignmentPost = !!msg.project_id && !isMyMsg && !msg.is_system_msg;
  const isClaimed = !!msg.claimed_by_resource_id;
  const isMe = isMyMsg;

  async function handleClaim() {
    setClaiming(true);
    try { await onClaim(msg.event_id); }
    finally { setClaiming(false); }
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: alignRight ? "row-reverse" : "row",
        gap: 1.5,
        mb: 2,
        alignItems: "flex-start",
      }}
    >
      <Avatar
        sx={{
          width: 32, height: 32, fontSize: 12, fontWeight: 700, flexShrink: 0,
          bgcolor: isMe ? "#3b82d4" : "#1f2328",
        }}
      >
        {initials(msg.sender)}
      </Avatar>

      <Box sx={{ maxWidth: "72%", minWidth: 180 }}>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ mb: 0.5, display: "block", textAlign: alignRight ? "right" : "left" }}
        >
          {msg.sender}
        </Typography>

        <Box
          sx={{
            p: 1.5,
            borderRadius: alignRight ? "12px 4px 12px 12px" : "4px 12px 12px 12px",
            bgcolor: alignRight ? "#e8f0fe" : "#f7f8fa",
            border: "1px solid",
            borderColor: alignRight ? "#c7d7fc" : "#e5e7eb",
          }}
        >
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            {msg.text}
          </Typography>

          {/* Project tags — any message that extracted a project */}
          {isAssignmentPost && (
            <Box sx={{ mt: 1, display: "flex", flexWrap: "wrap", gap: 0.5 }}>
              <Chip label={`📋 ${msg.project_name}`} size="small" color="primary" sx={{ fontSize: 11 }} />
              {msg.customer && (
                <Chip label={`🏢 ${msg.customer}`} size="small" variant="outlined" sx={{ fontSize: 11 }} />
              )}
              {msg.skills.slice(0, 3).map((s) => (
                <Chip key={s} label={s} size="small" color="secondary" variant="outlined" sx={{ fontSize: 11 }} />
              ))}
            </Box>
          )}

          {/* Claim area — any assignment post */}
          {isAssignmentPost && (
            <Box sx={{ mt: 1.5 }}>
              {isClaimed ? (
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <CheckCircleOutlinedIcon sx={{ fontSize: 14, color: "#2eb67d" }} />
                  <Typography variant="caption" sx={{ color: "#2eb67d", fontWeight: 600 }}>
                    {`Claimed by ${msg.claimed_by_name ?? "someone"}`}
                    {msg.mentioned_name ? ` (via @${msg.mentioned_name})` : ""}
                  </Typography>
                </Box>
              ) : !isAdmin ? (
                <Box sx={{ display: "flex", gap: 0.75, flexWrap: "wrap" }}>
                  <Button
                    size="small"
                    variant="outlined"
                    color="success"
                    onClick={handleClaim}
                    disabled={claiming}
                    startIcon={claiming ? <CircularProgress size={12} /> : <CheckCircleOutlinedIcon />}
                    sx={{ fontSize: 11, py: 0.25 }}
                  >
                    {claiming ? "Claiming…" : "Claim this task"}
                  </Button>
                  <Button
                    size="small"
                    variant="text"
                    onClick={() => onReply(msg)}
                    sx={{ fontSize: 11, py: 0.25, color: "#57606a" }}
                  >
                    ↩ Reply
                  </Button>
                </Box>
              ) : (
                <Box sx={{ display: "flex", gap: 0.75, alignItems: "center" }}>
                  <Typography variant="caption" color="text.secondary">
                    Unclaimed — switch to User mode to claim
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* My reply that claimed a project */}
          {isMyMsg && msg.project_id && (
            <Box sx={{ mt: 0.75, display: "flex", alignItems: "center", gap: 0.5 }}>
              <CheckCircleOutlinedIcon sx={{ fontSize: 13, color: "#2eb67d" }} />
              <Typography variant="caption" sx={{ color: "#2eb67d" }}>
                Claimed: {msg.project_name}
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}

// ── Name prompt dialog ────────────────────────────────────────────────────────

function NamePrompt({
  open,
  onConfirm,
}: {
  open: boolean;
  onConfirm: (name: string) => void;
}) {
  const [val, setVal] = useState("");
  return (
    <Dialog open={open} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ fontSize: 15 }}>Who are you?</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Enter your name to participate in the conversation as a User.
        </Typography>
        <TextField
          autoFocus
          fullWidth
          size="small"
          label="Your name"
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && val.trim()) onConfirm(val.trim()); }}
        />
      </DialogContent>
      <DialogActions>
        <Button
          variant="contained"
          disabled={!val.trim()}
          onClick={() => onConfirm(val.trim())}
        >
          Continue
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

const USER_NAME_KEY = "sim_user_name";

export default function SlackSimulator({ onProjectCreated }: Props) {
  const { role, isAdmin } = useRole();
  const [messages, setMessages] = useState<SimMessage[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [namePromptOpen, setNamePromptOpen] = useState(false);
  const [replyingTo, setReplyingTo] = useState<SimMessage | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load persisted user name from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(USER_NAME_KEY);
    if (stored) setUserName(stored);
  }, []);

  // When switching to User mode and no name set, prompt
  useEffect(() => {
    if (!isAdmin && !userName) setNamePromptOpen(true);
  }, [isAdmin, userName]);

  const loadMessages = useCallback(async () => {
    try {
      const msgs = await apiFetch<SimMessage[]>("/slack/messages", role);
      setMessages(msgs);
    } catch { /* silently ignore */ }
  }, [role]);

  useEffect(() => { loadMessages(); }, [loadMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleNameConfirm(name: string) {
    setUserName(name);
    localStorage.setItem(USER_NAME_KEY, name);
    setNamePromptOpen(false);
  }

  const senderName = isAdmin ? "Admin" : (userName ?? "User");

  function handleReply(msg: SimMessage) {
    setReplyingTo(msg);
    // Focus the input
    setTimeout(() => inputRef.current?.focus(), 50);
  }

  async function handleSend() {
    if (!text.trim()) return;
    if (!isAdmin && !userName) {
      setNamePromptOpen(true);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const body: Record<string, unknown> = { text: text.trim(), user: senderName };
      if (!isAdmin && replyingTo) {
        body.reply_to_event_id = replyingTo.event_id;
      }
      await apiFetch<SimMessage>("/slack/simulate", role, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setText("");
      setReplyingTo(null);
      await loadMessages();
      onProjectCreated?.();
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleClaim(eventId: string) {
    if (!userName && !isAdmin) {
      setNamePromptOpen(true);
      return;
    }
    const updated = await apiFetch<SimMessage>(`/slack/claim/${eventId}`, role, {
      method: "POST",
      body: JSON.stringify({ name: senderName }),
    });
    // Refresh all messages so the admin msg's claim status also updates
    const all = await apiFetch<SimMessage[]>("/slack/messages", role);
    setMessages(all);
    onProjectCreated?.();
  }

  const placeholder = isAdmin
    ? 'e.g. "Hey @Adam, Storage Scale SME needed for ABC Corp by July 31st"'
    : 'Reply… e.g. "I\'ll take it" or "Sure, on it" to claim an open task';

  const helperText = isAdmin
    ? "Cmd+Enter to send · @mention a person to auto-assign"
    : "Affirmative replies (\"yes\", \"I'll do it\", etc.) auto-claim the latest open task";

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "calc(100vh - 160px)", minHeight: 400 }}>
      {/* ── Role banner ── */}
      <Box
        sx={{
          px: 2, py: 1, bgcolor: isAdmin ? "#1f2328" : "#e8f0fe",
          borderRadius: 1, mb: 2, display: "flex", alignItems: "center", gap: 1,
        }}
      >
        <Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: isAdmin ? "#E01E5A" : "#3b82d4" }} />
        <Typography variant="caption" sx={{ color: isAdmin ? "#fff" : "#1f2328", fontWeight: 600 }}>
          {isAdmin
            ? "Admin — send assignment requests. @mention a person to auto-assign them."
            : `Chatting as ${userName ?? "…"}. Reply to claim tasks, or click the Claim button.`}
        </Typography>
        {!isAdmin && userName && (
          <Button
            size="small"
            sx={{ ml: "auto", fontSize: 10, color: "#57606a", minWidth: 0 }}
            onClick={() => setNamePromptOpen(true)}
          >
            Change name
          </Button>
        )}
      </Box>

      {/* ── Sample chips — admin only ── */}
      {isAdmin && (
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mb: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ width: "100%", mb: 0.25 }}>
            Try a sample:
          </Typography>
          {ADMIN_SAMPLES.map((s, i) => (
            <Chip
              key={i}
              label={s.slice(0, 55) + "…"}
              size="small"
              variant="outlined"
              onClick={() => setText(s)}
              sx={{ fontSize: 11, cursor: "pointer" }}
            />
          ))}
        </Box>
      )}

      {/* ── Thread ── */}
      <Box
        sx={{
          flex: 1, overflowY: "auto", px: 1.5, py: 1.5,
          border: "1px solid #e5e7eb", borderRadius: 1, bgcolor: "#fff", mb: 2,
        }}
      >
        {messages.length === 0 ? (
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
            <Typography variant="body2" color="text.secondary">
              No messages yet. Switch to Admin and send a message to get started.
            </Typography>
          </Box>
        ) : (
          // AC1 — sort by created_at ascending (safety net on top of server ordering)
          [...messages]
            .sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? ""))
            .map((msg) =>
              msg.is_system_msg ? (
                <SystemMessage key={msg.event_id} text={msg.text} />
              ) : (
                <MessageBubble
                  key={msg.event_id}
                  msg={msg}
                  isAdmin={isAdmin}
                  currentUserName={userName}
                  onClaim={handleClaim}
                  onReply={handleReply}
                />
              )
            )
        )}
        <div ref={bottomRef} />
      </Box>

      {/* ── Reply context bar ── */}
      {!isAdmin && replyingTo && (
        <Box
          sx={{
            display: "flex", alignItems: "center", gap: 1,
            px: 1.5, py: 0.75, mb: 0.5,
            bgcolor: "#f0f4ff", border: "1px solid #c7d7fc",
            borderRadius: 1, borderLeft: "3px solid #3b82d4",
          }}
        >
          <Typography variant="caption" sx={{ flex: 1, color: "#1f2328" }}>
            <strong>Replying to:</strong> {replyingTo.project_name ?? replyingTo.text.slice(0, 60)}
          </Typography>
          <Button
            size="small"
            sx={{ fontSize: 10, minWidth: 0, color: "#57606a", p: 0.25 }}
            onClick={() => setReplyingTo(null)}
          >
            ✕ Cancel
          </Button>
        </Box>
      )}

      {/* ── Input — both roles ── */}
      <Box sx={{ display: "flex", gap: 1, alignItems: "flex-start" }}>
        <TextField
          fullWidth
          multiline
          minRows={2}
          maxRows={5}
          placeholder={
            !isAdmin && replyingTo
              ? `Reply to ${replyingTo.project_name ?? "this task"}… Your reply will claim it.`
              : placeholder
          }
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSend(); }}
          size="small"
          helperText={helperText}
          slotProps={{ input: { inputRef } }}
        />
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={14} color="inherit" /> : <SendIcon />}
          onClick={handleSend}
          disabled={loading || !text.trim()}
          sx={{ minWidth: 90, mt: 0.5 }}
          color={isAdmin ? "primary" : "success"}
        >
          {loading ? "…" : "Send"}
        </Button>
      </Box>

      <NamePrompt open={namePromptOpen} onConfirm={handleNameConfirm} />

      <Snackbar open={!!error} autoHideDuration={5000} onClose={() => setError(null)}>
        <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>
      </Snackbar>
    </Box>
  );
}
