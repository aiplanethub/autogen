import React, { useState } from "react";
import { Textarea, Button } from "@headlessui/react";
import Modal from "./Modal";
import GalleryModalScreen from "./GalleryModalScreen";
import ToolsModalScreen from "./options/ToolsModalScreen";
import Icon from "../../Icon";

type GalleryType = {
  id: string;
  name: string;
};

const TaskRequirementInput = () => {
  const [taskRequirement, setTaskRequirement] = useState("");
  const [modalScreen, setModalScreen] = useState<
    "gallery" | "tools" | "agents"
  >("gallery");
  const [isOpen, setIsOpen] = useState(false);
  const [selectedGallery, setSelectedGallery] = useState<GalleryType | null>(
    null
  );

  const onClose = () => {
    setIsOpen(false);
    setModalScreen("gallery");
  };

  const handleSelectGallery = (gallery: GalleryType) => {
    setSelectedGallery(gallery);
    setIsOpen(false);
  };

  const onOptionClick = (modalScreen: "gallery" | "tools" | "agents") => {
    setModalScreen(modalScreen);
    setIsOpen(true);
  };

  return (
    <div className="flex flex-col justify-center items-center w-full h-full">
      <h1 className="text-3xl font-semibold text-center text-black mb-6">
        Build Smart <span className="text-[#115E59]">AI Agents</span> in
        seconds!
      </h1>

      <div className="border-2 border-[#115E59] p-4 shadow-sm max-w-[815px] w-full rounded-[20px]">
        <Textarea
          className="w-full p-3 focus:ring-0 focus:outline-none text-base font-normal placeholder:text-gray-400 mb-3"
          placeholder="Type a prompt to complete a task"
          rows={3}
          value={taskRequirement}
          onChange={(e) => setTaskRequirement(e.target.value)}
        />

        <div className="flex items-center justify-between">
          <div className="flex space-x-2">
            <Button
              onClick={() => {}}
              className="w-8 h-8 rounded-full hover:bg-gray-100 transition-colors border flex justify-center items-center"
            >
              <Icon name="paperclip" className="h-4 w-4" />
            </Button>

            <Button className="h-8 px-3 rounded-full hover:bg-gray-100 transition-colors flex items-center border">
              <Icon name="sparkles" className="h-4 w-4 mr-2" />
              <span className="text-sm font-normal">Prompts</span>
            </Button>

            <Button
              onClick={() => onOptionClick("agents")}
              className="px-3 h-8 rounded-full hover:bg-gray-100 transition-colors flex items-center border"
            >
              <Icon name="users" className="h-4 w-4 mr-2" />
              <span className="text-sm font-normal">Agents</span>
            </Button>

            <Button
              onClick={() => onOptionClick("tools")}
              className="px-3 h-8 rounded-full hover:bg-gray-100 transition-colors flex items-center border"
            >
              {/* <Tool className="h-5 w-5 mr-2" /> */}
              <span className="text-sm font-normal">Tools</span>
            </Button>
          </div>

          <Button className="bg-[#115E59] hover:bg-green-800 text-white py-2 px-4 rounded-lg flex items-center transition-colors font-medium text-sm">
            <Icon name="send" className="h-4 w-4 mr-2" />
            Build Agent
          </Button>
        </div>
      </div>

      {isOpen && (
        <Modal
          isOpen={isOpen}
          onClose={onClose}
          title={`Select ${modalScreen}`}
        >
          {modalScreen === "gallery" ? (
            <GalleryModalScreen
              onSelectGallery={handleSelectGallery}
              selectedGallery={selectedGallery}
            />
          ) : modalScreen === "tools" ? (
            <ToolsModalScreen />
          ) : (
            <></>
          )}
        </Modal>
      )}
    </div>
  );
};

export default TaskRequirementInput;
