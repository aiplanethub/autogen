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
