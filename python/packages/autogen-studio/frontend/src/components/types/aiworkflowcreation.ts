export type GalleryType = {
  id: string;
  name: string;
};

export interface AgentAndToolProps {
  id: string | undefined;
  name: string | undefined;
  enabled: boolean;
}

export type ModalScreens = "gallery" | "tools" | "agents" | "prompts";
export type PromptCategory = "MARKETING" | "EDUCATION" | "BANKING";

export interface IPrompt {
  id: string;
  category: PromptCategory;
  content: string;
}

export interface IGalleryProps {
  id: number | undefined;
  name: string;
  agents: Array<AgentAndToolProps>;
  tools: Array<AgentAndToolProps>;
}

export interface IAIWorkflowCreationSidebarProps {
  isOpen: boolean;
  sessions: Array<IAIWorkflowCreationSession>;
  currentSession: IAIWorkflowCreationSession | null;
  onToggle: () => void;
  onSelectSession: (session: IAIWorkflowCreationSession) => void;
  onCreateSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  isLoading?: boolean;
}

export type AIWorkflowCreationRoleType = "user" | "assistant" | "system";

export interface IAIWorkflowCreationMessage {
  role: AIWorkflowCreationRoleType;
  content: string;
  message_meta: Object;
  builder_session_id: number;
}
export interface IAIWorkflowCreationConfig {
  agents: Array<string>;
  tools: Array<string>;
  knowledgebases: Array<string>;
  gallery_id: number;
  builder_session_id: number;
}
export interface IAIWorkflowCreationSession {
  id: string;
  name: string;
  summary: string | undefined;
  workflow_config: Object | undefined;
  messages: Array<IAIWorkflowCreationMessage>;
  config: IAIWorkflowCreationConfig;
}
