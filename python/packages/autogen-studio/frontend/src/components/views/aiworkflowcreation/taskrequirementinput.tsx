import React, { useState } from "react";
import { Paperclip, Sparkles, Users, Send } from "lucide-react";
import { Textarea, Button } from "@headlessui/react";
import Modal from "./Modal";
import GalleryModalScreen from "./GalleryModalScreen";

type GalleryType = {
  id: string;
  name: string;
};

const TaskRequirementInput = () => {
  const [taskRequirement, setTaskRequirement] = useState("");
  const [isGalleryModalOpen, setIsGalleryModalOpen] = useState(false);
  const [selectedGallery, setSelectedGallery] = useState<GalleryType | null>(
    null
  );

  const onGalleryModalClose = () => {
    setIsGalleryModalOpen(false);
  };

  const handleSelectGallery = (gallery: GalleryType) => {
    setSelectedGallery(gallery);
    setIsGalleryModalOpen(false);
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
              onClick={() => setIsGalleryModalOpen(true)}
              className="w-8 h-8 rounded-full hover:bg-gray-100 transition-colors border flex justify-center items-center"
            >
              <Paperclip className="h-4 w-4" />
            </Button>

            <Button className="h-8 px-3 rounded-full hover:bg-gray-100 transition-colors flex items-center border">
              <Sparkles className="h-4 w-4 mr-2" />
              <span className="text-sm font-normal">Prompts</span>
            </Button>

            <Button className="px-3 h-8 rounded-full hover:bg-gray-100 transition-colors flex items-center border">
              <Users className="h-4 w-4 mr-2" />
              <span className="text-sm font-normal">Agents</span>
            </Button>

            <Button
              onClick={() => setIsGalleryModalOpen(true)}
              className="px-3 h-8 rounded-full hover:bg-gray-100 transition-colors flex items-center border"
            >
              {/* <Tool className="h-5 w-5 mr-2" /> */}
              <span className="text-sm font-normal">Tools</span>
            </Button>
          </div>

          <Button className="bg-[#115E59] hover:bg-green-800 text-white py-2 px-4 rounded-lg flex items-center transition-colors font-medium text-sm">
            <Send className="h-4 w-4 mr-2" />
            Build Agent
          </Button>
        </div>
      </div>

      <Modal
        isOpen={isGalleryModalOpen}
        onClose={onGalleryModalClose}
        title="Select Gallery"
      >
        <GalleryModalScreen
          onSelectGallery={handleSelectGallery}
          selectedGallery={selectedGallery}
        />
      </Modal>
    </div>
  );
};

export default TaskRequirementInput;
