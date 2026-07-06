"use client";

import React, { createContext, useContext, useState } from "react";

type Role = "admin" | "user";

interface RoleContextValue {
  role: Role;
  setRole: (r: Role) => void;
  isAdmin: boolean;
}

const RoleContext = createContext<RoleContextValue>({
  role: "admin",
  setRole: () => {},
  isAdmin: true,
});

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<Role>("admin");
  return (
    <RoleContext.Provider value={{ role, setRole, isAdmin: role === "admin" }}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  return useContext(RoleContext);
}
