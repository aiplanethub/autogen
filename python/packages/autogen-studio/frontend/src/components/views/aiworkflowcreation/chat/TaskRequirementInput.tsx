import React, { useCallback, useContext, useEffect, useState } from "react";
import { Textarea, Button } from "@headlessui/react";
import Modal from "../Modal";
import GalleryModalScreen from "../GalleryModalScreen";
import ToolsModalScreen from "../options/ToolsModalScreen";
import Icon from "../../../Icon";
import AgentsModalScreen from "../options/AgentsModalScreen";
import { message } from "antd";
import {
  IGalleryProps,
  IPrompt,
  ModalScreens,
} from "../../../types/aiworkflowcreation";
import { appContext } from "../../../../hooks/provider";
import { galleryAPI } from "../../gallery/api";
import PromptModal from "../options/prompts/PromptModal";
import { cn } from "../../../utils/utils";

const TaskRequirementInput: React.FC<{ hasConversations: boolean }> = ({
  hasConversations,
}) => {
  const [messageApi, contextHolder] = message.useMessage();
  const [isLoading, setIsLoading] = useState(false);
  const [galleries, setGalleries] = useState<IGalleryProps[]>([]);
  const [taskRequirement, setTaskRequirement] = useState("");
  const [modalScreen, setModalScreen] = useState<ModalScreens>("gallery");
  const [isOpen, setIsOpen] = useState(false);
  const [selectedGallery, setSelectedGallery] = useState<IGalleryProps | null>(
    null
  );
  const [selectedPrompt, setSelectedPrompt] = useState<IPrompt | null>(null);
  const { user } = useContext(appContext);
  const fetchGalleries = useCallback(async () => {
    if (!user?.id) return;
    try {
      setIsLoading(true);
      const response = await galleryAPI.listGalleries(user.id);
      const data = response.map((item) => ({
        id: item.id,
        name: item.config.name,
        agents: item.config.components.agents.map((agent) => ({
          id: !!agent.config.name ? agent.config.name : agent.label,
          name: agent.label,
          enabled: false,
        })),
        tools: item.config.components.tools.map((tool) => ({
          id: !!tool.config.name ? tool.config.name : tool.label,
          name: tool.label,
          enabled: false,
        })),
      }));
      setGalleries(data);
    } catch (error) {
      console.error("Error fetching galleries:", error);
      messageApi.error("Failed to fetch galleries");
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, messageApi]);

  useEffect(() => {
    fetchGalleries();
  }, [fetchGalleries]);

  const onClose = () => {
    setIsOpen(false);
    setModalScreen("gallery");
  };

  const onSelectGallery = (gallery: IGalleryProps) => {
    setSelectedGallery(gallery);
    setIsOpen(false);
  };

  const onOptionClick = (modalScreen: ModalScreens) => {
    if (selectedGallery == null && modalScreen !== "prompts") {
      setModalScreen("gallery");
      messageApi.error(
        "Please select a Gallery before selecting Tools or Agents!."
      );
    } else {
      setModalScreen(modalScreen);
    }
    setIsOpen(true);
  };

  const onChangeGallery = () => {
    setModalScreen("gallery");
  };

  const onToggleTool = (id: string) => {
    if (selectedGallery === null) return;
    setSelectedGallery({
      ...selectedGallery,
      tools: selectedGallery.tools.map((tool) =>
        tool.id === id ? { ...tool, enabled: !tool.enabled } : tool
      ),
    });
  };

  const onToggleAgent = (id: string) => {
    if (selectedGallery === null) return;
    setSelectedGallery({
      ...selectedGallery,
      agents: selectedGallery.agents.map((agent) =>
        agent.id === id ? { ...agent, enabled: !agent.enabled } : agent
      ),
    });
  };

  const onSelectPrompt = (prompt: IPrompt) => {
    setSelectedPrompt(prompt);
    setIsOpen(false);
  };

  return (
    <div
      className={cn(
        "flex flex-col justify-center items-center w-full",
        hasConversations ? "h-auto" : "h-full"
      )}
    >
      {contextHolder}
      {!hasConversations && (
        <h1 className="text-3xl font-semibold text-center mb-6">
          Build Smart <span className="text-[#115E59]">AI Agents</span> in
          seconds!
        </h1>
      )}

      <div
        className={cn(
          "border border-[#115E59] p-4 shadow-sm max-w-[815px] w-full rounded-[20px]"
        )}
      >
        <Textarea
          className="w-full p-3 focus:ring-0 focus:outline-none text-base bg-transparent font-normal placeholder:text-gray-400 mb-3"
          placeholder="Type a prompt to complete a task"
          rows={hasConversations ? 1 : 3}
          value={taskRequirement}
          onChange={(e) => setTaskRequirement(e.target.value)}
        />

        <div className="flex items-center justify-between">
          <div className="flex space-x-2">
            <Button
              onClick={() => {}}
              className="w-8 h-8 rounded-full hover:bg-secondary transition-colors border border-secondary flex justify-center items-center"
            >
              <Icon name="paperclip" className="h-4 w-4" />
            </Button>

            <Button
              onClick={() => onOptionClick("prompts")}
              className="h-8 px-3 rounded-full hover:bg-secondary transition-colors flex items-center border border-secondary"
            >
              <Icon name="sparkles" className="h-4 w-4 mr-2" />
              <span className="text-sm font-normal">Prompts</span>
            </Button>

            <Button
              onClick={() => onOptionClick("agents")}
              className="px-3 h-8 rounded-full hover:bg-secondary transition-colors flex items-center border border-secondary"
            >
              <Icon name="users" className="h-4 w-4 mr-2" />
              <span className="text-sm font-normal">Agents</span>
            </Button>

            <Button
              onClick={() => onOptionClick("tools")}
              className="px-3 h-8 rounded-full hover:bg-secondary transition-colors flex items-center border border-secondary"
            >
              {/* <Tool className="h-5 w-5 mr-2" /> */}
              <span className="text-sm font-normal">Tools</span>
            </Button>
          </div>

          <Button
            className={cn(
              "bg-[#115E59] hover:bg-green-800 text-white py-2 px-4 rounded-lg flex items-center transition-colors font-medium text-sm",
              hasConversations && "px-2"
            )}
          >
            <Icon
              name="send"
              className={cn("h-4 w-4", !hasConversations && "mr-2")}
            />
            {!hasConversations && "Build Agent"}
          </Button>
        </div>
      </div>

      {isOpen && modalScreen !== "prompts" && (
        <Modal
          isOpen={isOpen}
          onClose={onClose}
          title={`Select ${modalScreen}`}
        >
          {modalScreen === "gallery" && (
            <GalleryModalScreen
              galleries={galleries}
              onSelectGallery={onSelectGallery}
              selectedGallery={selectedGallery}
            />
          )}
          {!!selectedGallery &&
            modalScreen !== "gallery" &&
            (modalScreen === "tools" ? (
              <ToolsModalScreen
                selectedGallery={selectedGallery.name}
                onChangeGallery={onChangeGallery}
                tools={selectedGallery.tools}
                onToggleTool={onToggleTool}
              />
            ) : (
              <AgentsModalScreen
                selectedGallery={selectedGallery.name}
                onChangeGallery={onChangeGallery}
                agents={selectedGallery.agents}
                onToggleAgent={onToggleAgent}
              />
            ))}
        </Modal>
      )}

      {isOpen && modalScreen === "prompts" && (
        <PromptModal
          isOpen={isOpen}
          onClose={onClose}
          selectedPrompt={!!selectedPrompt ? selectedPrompt : null}
          onSelectPrompt={onSelectPrompt}
        />
      )}
    </div>
  );
};

export default TaskRequirementInput;
