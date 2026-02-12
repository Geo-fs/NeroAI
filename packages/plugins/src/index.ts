export interface ToolPermissionRequirement {
  permission: string;
  pathScoped?: boolean;
}

export interface ToolPluginContract {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  permissionRequirements: ToolPermissionRequirement[];
}
