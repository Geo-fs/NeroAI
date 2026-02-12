import { z } from "zod";

export const permissionTypeSchema = z.enum([
  "filesystem.read",
  "filesystem.write",
  "web.search",
  "clipboard.read",
  "clipboard.write",
  "process.run"
]);

export const grantScopeSchema = z.enum(["once", "session", "always"]);

export const modelSourceSchema = z.object({
  id: z.string(),
  name: z.string(),
  baseUrl: z.string().url(),
  authToken: z.string().optional(),
  isLocal: z.boolean().default(false)
});

export const workflowStepSchema = z.object({
  id: z.string(),
  type: z.enum(["prompt_agent", "call_tool", "set_variable"]),
  config: z.record(z.any())
});

export const workflowSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().default(""),
  steps: z.array(workflowStepSchema)
});

export const uiComponentSchema = z.object({
  id: z.string(),
  type: z.enum(["text", "button", "input", "toggle", "card", "table"]),
  props: z.record(z.any()).default({}),
  binding: z.record(z.any()).optional()
});

export const uiLayoutSchema = z.object({
  id: z.string(),
  name: z.string(),
  components: z.array(uiComponentSchema),
  createdAt: z.string().optional(),
  updatedAt: z.string().optional()
});

export type PermissionType = z.infer<typeof permissionTypeSchema>;
export type GrantScope = z.infer<typeof grantScopeSchema>;
export type ModelSource = z.infer<typeof modelSourceSchema>;
export type WorkflowDefinition = z.infer<typeof workflowSchema>;
export type UiLayout = z.infer<typeof uiLayoutSchema>;
